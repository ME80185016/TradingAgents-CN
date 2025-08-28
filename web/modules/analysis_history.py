"""
分析历史记录模块
提供查看、管理和恢复历史分析记录的功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from web.utils.async_progress_tracker import get_all_analysis_history, get_progress_by_id
from web.utils.analysis_runner import format_analysis_results
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('analysis_history')


def render_analysis_history():
    """渲染分析历史记录页面"""
    st.header("📈 历史记录")
    st.markdown("查看和管理您的股票分析历史记录")

    # 添加刷新按钮和筛选选项
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        record_limit = st.selectbox(
            "显示数量",
            [20, 50, 100, 200],
            index=1,  # 默认50条
            help="选择要显示的历史记录数量"
        )
    
    with col2:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "已完成", "运行中", "失败"],
            help="根据分析状态筛选记录"
        )
    
    with col3:
        time_filter = st.selectbox(
            "时间范围",
            ["全部", "今天", "最近7天", "最近30天"],
            help="根据时间范围筛选记录"
        )
    
    with col4:
        if st.button("🔄 刷新", help="刷新历史记录列表"):
            st.rerun()

    # 获取历史记录
    with st.spinner("📊 正在获取历史记录..."):
        try:
            history_records = get_all_analysis_history(limit=record_limit)
        except Exception as e:
            st.error(f"❌ 获取历史记录失败: {e}")
            logger.error(f"获取历史记录失败: {e}")
            return

    if not history_records:
        st.info("📝 暂无历史记录。开始您的第一个股票分析吧！")
        if st.button("🚀 开始分析", type="primary"):
            st.switch_page("pages/stock_analysis.py")
        return

    # 应用筛选
    filtered_records = apply_filters(history_records, status_filter, time_filter)
    
    if not filtered_records:
        st.warning("🔍 没有符合筛选条件的记录")
        return

    # 显示统计信息
    display_statistics(filtered_records)
    
    st.markdown("---")
    
    # 显示历史记录列表
    display_history_table(filtered_records)


def apply_filters(records: List[Dict], status_filter: str, time_filter: str) -> List[Dict]:
    """应用筛选条件"""
    filtered = records.copy()
    
    # 状态筛选
    if status_filter != "全部":
        status_map = {
            "已完成": "completed",
            "运行中": "running", 
            "失败": "failed"
        }
        target_status = status_map.get(status_filter)
        if target_status:
            filtered = [r for r in filtered if r.get('status') == target_status]
    
    # 时间筛选
    if time_filter != "全部":
        now = datetime.now()
        
        if time_filter == "今天":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_timestamp = start_of_day.timestamp()
        elif time_filter == "最近7天":
            cutoff_timestamp = (now - timedelta(days=7)).timestamp()
        elif time_filter == "最近30天":
            cutoff_timestamp = (now - timedelta(days=30)).timestamp()
        else:
            cutoff_timestamp = 0
        
        filtered = [r for r in filtered if r.get('last_update', 0) >= cutoff_timestamp]
    
    return filtered


def display_statistics(records: List[Dict]):
    """显示统计信息"""
    if not records:
        return
    
    st.subheader("📊 统计概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 总记录数
    with col1:
        st.metric("总记录数", len(records))
    
    # 已完成数量
    with col2:
        completed_count = len([r for r in records if r.get('status') == 'completed'])
        st.metric("已完成", completed_count, f"{completed_count/len(records)*100:.1f}%")
    
    # 运行中数量
    with col3:
        running_count = len([r for r in records if r.get('status') == 'running'])
        st.metric("运行中", running_count)
    
    # 失败数量  
    with col4:
        failed_count = len([r for r in records if r.get('status') == 'failed'])
        st.metric("失败", failed_count, f"{failed_count/len(records)*100:.1f}%" if failed_count > 0 else "0%")


def display_history_table(records: List[Dict]):
    """显示历史记录表格"""
    st.subheader("📋 历史记录列表")
    
    # 准备表格数据
    table_data = []
    for record in records:
        table_data.append({
            "股票代码": record.get('stock_symbol', '未知'),
            "市场": record.get('market_type', '未知'),
            "状态": f"{record.get('status_icon', '❓')} {record.get('status_text', '未知')}",
            "进度": f"{record.get('progress_percentage', 0):.1f}%",
            "开始时间": record.get('start_time_formatted', '未知'),
            "耗时": record.get('duration_formatted', '未知'),
            "分析师": ', '.join(record.get('analysts', [])) if record.get('analysts') else '未知',
            "研究深度": get_depth_text(record.get('research_depth')),
            "操作": "action_buttons"  # 占位符，实际按钮在下面单独处理
        })
    
    if not table_data:
        st.info("📝 没有要显示的记录")
        return
    
    # 创建DataFrame
    df = pd.DataFrame(table_data)
    
    # 显示表格（不包含操作列）
    display_df = df.drop('操作', axis=1)
    
    # 配置表格样式
    styled_df = display_df.style.apply(style_status_row, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    
    # 显示操作按钮区域
    display_action_buttons(records)


def style_status_row(row):
    """为表格行应用状态样式"""
    styles = [''] * len(row)
    
    status_text = row['状态']
    if '✅' in status_text:
        # 已完成 - 绿色背景
        styles = ['background-color: #d4edda'] * len(row)
    elif '🔄' in status_text:
        # 运行中 - 蓝色背景
        styles = ['background-color: #d1ecf1'] * len(row)
    elif '❌' in status_text:
        # 失败 - 红色背景
        styles = ['background-color: #f8d7da'] * len(row)
    
    return styles


def display_action_buttons(records: List[Dict]):
    """显示操作按钮"""
    st.subheader("🔧 快速操作")
    
    # 选择要操作的记录
    if not records:
        return
    
    # 创建选择框选项
    options = []
    for i, record in enumerate(records):
        stock = record.get('stock_symbol', '未知')
        status = record.get('status_text', '未知')
        time_str = record.get('last_update_formatted', '未知')
        options.append(f"{stock} - {status} - {time_str}")
    
    selected_index = st.selectbox(
        "选择要操作的记录",
        range(len(options)),
        format_func=lambda x: options[x],
        help="选择一条历史记录进行操作"
    )
    
    if selected_index is not None:
        selected_record = records[selected_index]
        display_record_actions(selected_record)


def display_record_actions(record: Dict):
    """显示单条记录的操作选项"""
    analysis_id = record.get('analysis_id')
    status = record.get('status')
    has_results = record.get('has_results', False)
    
    st.markdown(f"**选中记录**: {record.get('stock_symbol')} ({record.get('status_text')})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 查看详情
    with col1:
        if st.button("📊 查看详情", key=f"details_{analysis_id}"):
            display_record_details(record)
    
    # 查看报告（仅已完成的分析）
    with col2:
        if status == 'completed' and has_results:
            if st.button("📋 查看报告", key=f"report_{analysis_id}", type="primary"):
                load_and_display_report(analysis_id)
        else:
            st.button("📋 查看报告", disabled=True, help="只有已完成的分析才能查看报告")
    
    # 重新分析
    with col3:
        if st.button("🔄 重新分析", key=f"rerun_{analysis_id}"):
            setup_reanalysis(record)
    
    # 删除记录
    with col4:
        if st.button("🗑️ 删除", key=f"delete_{analysis_id}"):
            confirm_delete_record(analysis_id)


def display_record_details(record: Dict):
    """显示记录详情"""
    st.subheader(f"📊 详细信息 - {record.get('stock_symbol')}")
    
    # 基本信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**分析ID**: `{record.get('analysis_id')}`")
        st.markdown(f"**股票代码**: {record.get('stock_symbol')}")
        st.markdown(f"**市场类型**: {record.get('market_type')}")
        st.markdown(f"**状态**: {record.get('status_icon')} {record.get('status_text')}")
        st.markdown(f"**进度**: {record.get('progress_percentage', 0):.1f}%")
    
    with col2:
        st.markdown(f"**开始时间**: {record.get('start_time_formatted')}")
        st.markdown(f"**最后更新**: {record.get('last_update_formatted')}")
        st.markdown(f"**持续时间**: {record.get('duration_formatted')}")
        st.markdown(f"**分析师**: {', '.join(record.get('analysts', []))}")
        st.markdown(f"**研究深度**: {get_depth_text(record.get('research_depth'))}")

    # 获取更详细的进度信息
    analysis_id = record.get('analysis_id')
    try:
        progress_data = get_progress_by_id(analysis_id)
        if progress_data:
            st.markdown("---")
            st.subheader("📈 详细进度")
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown(f"**当前步骤**: {progress_data.get('current_step_name', '未知')}")
                st.markdown(f"**步骤描述**: {progress_data.get('current_step_description', '无')}")
                st.markdown(f"**最后消息**: {progress_data.get('last_message', '无')}")
            
            with col4:
                steps = progress_data.get('steps', [])
                if steps:
                    st.markdown("**分析步骤**:")
                    for i, step in enumerate(steps):
                        current = i == progress_data.get('current_step', 0)
                        icon = "▶️" if current else ("✅" if i < progress_data.get('current_step', 0) else "⏸️")
                        st.markdown(f"{icon} {step.get('name', f'步骤{i+1}')}")
    
    except Exception as e:
        st.error(f"获取详细进度失败: {e}")


def load_and_display_report(analysis_id: str):
    """加载并显示分析报告"""
    try:
        st.subheader("📋 分析报告")
        
        # 获取进度数据
        progress_data = get_progress_by_id(analysis_id)
        if not progress_data:
            st.error("❌ 无法获取分析数据")
            return
        
        raw_results = progress_data.get('raw_results')
        if not raw_results:
            st.error("❌ 分析结果不存在")
            return
        
        # 格式化结果
        formatted_results = format_analysis_results(raw_results)
        if not formatted_results:
            st.error("❌ 分析结果格式化失败")
            return
        
        # 恢复到session state以便使用现有的显示组件
        st.session_state.analysis_results = formatted_results
        st.session_state.current_analysis_id = analysis_id
        st.session_state.analysis_running = False
        
        st.success("✅ 报告已加载到主页面，请切换到「📊 股票分析」页面查看完整报告")
        
        # 显示简要摘要
        if formatted_results.get('decision'):
            decision = formatted_results['decision']
            st.markdown("### 📊 投资建议摘要")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**投资建议**: {decision.get('decision_type', '未知')}")
                st.markdown(f"**置信度**: {decision.get('confidence_level', '未知')}")
            with col2:
                st.markdown(f"**目标价格**: {decision.get('target_price', '未设定')}")
                st.markdown(f"**风险等级**: {decision.get('risk_level', '未知')}")
            
            if decision.get('summary'):
                st.markdown("**决策摘要**:")
                st.markdown(decision['summary'])
    
    except Exception as e:
        st.error(f"❌ 加载报告失败: {e}")
        logger.error(f"加载报告失败: {analysis_id}, 错误: {e}")


def setup_reanalysis(record: Dict):
    """设置重新分析"""
    st.subheader("🔄 重新分析设置")
    
    stock_symbol = record.get('stock_symbol')
    market_type = record.get('market_type', '美股')
    
    if not stock_symbol or stock_symbol == '未知股票':
        st.error("❌ 无法获取股票代码，无法重新分析")
        return
    
    st.info(f"📊 准备重新分析股票: {stock_symbol} ({market_type})")
    
    # 恢复到session state以便在主页面进行分析
    st.session_state.last_stock_symbol = stock_symbol
    st.session_state.last_market_type = market_type
    
    # 建议的分析配置
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**原分析配置**:")
        st.markdown(f"- 分析师: {', '.join(record.get('analysts', []))}")
        st.markdown(f"- 研究深度: {get_depth_text(record.get('research_depth'))}")
    
    with col2:
        st.markdown("**操作说明**:")
        st.markdown("1. 点击下方按钮跳转到分析页面")
        st.markdown("2. 股票代码将自动填入")
        st.markdown("3. 根据需要调整分析配置")
        st.markdown("4. 启动新的分析")
    
    if st.button("🚀 前往分析页面", type="primary"):
        st.switch_page("股票分析")  # 跳转到主分析页面


def confirm_delete_record(analysis_id: str):
    """确认删除记录"""
    st.subheader("🗑️ 删除确认")
    st.warning(f"您确定要删除分析记录 `{analysis_id}` 吗？")
    st.markdown("**注意**: 此操作将永久删除以下数据：")
    st.markdown("- 分析进度记录")
    st.markdown("- 分析结果（如果有）")
    st.markdown("- 相关的缓存文件")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ 确认删除", type="secondary"):
            delete_analysis_record(analysis_id)
    
    with col2:
        if st.button("🚫 取消", type="primary"):
            st.rerun()


def delete_analysis_record(analysis_id: str):
    """删除分析记录"""
    try:
        import os
        import redis
        
        success_count = 0
        error_messages = []
        
        # 删除文件记录
        try:
            progress_file = f"./data/progress_{analysis_id}.json"
            if os.path.exists(progress_file):
                os.remove(progress_file)
                success_count += 1
                logger.info(f"✅ 删除文件记录: {progress_file}")
        except Exception as e:
            error_messages.append(f"文件删除失败: {e}")
        
        # 删除Redis记录
        try:
            redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
            if redis_enabled:
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', 6379))
                redis_password = os.getenv('REDIS_PASSWORD', None)
                redis_db = int(os.getenv('REDIS_DB', 0))

                if redis_password:
                    redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        password=redis_password,
                        db=redis_db,
                        decode_responses=True
                    )
                else:
                    redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        db=redis_db,
                        decode_responses=True
                    )
                
                key = f"progress:{analysis_id}"
                result = redis_client.delete(key)
                if result > 0:
                    success_count += 1
                    logger.info(f"✅ 删除Redis记录: {key}")
                
        except Exception as e:
            error_messages.append(f"Redis删除失败: {e}")
        
        # 显示结果
        if success_count > 0:
            st.success(f"✅ 成功删除 {success_count} 项记录")
            if error_messages:
                for msg in error_messages:
                    st.warning(f"⚠️ {msg}")
            
            # 自动刷新页面
            st.rerun()
        else:
            st.error("❌ 删除失败，没有找到要删除的记录")
            for msg in error_messages:
                st.error(f"❌ {msg}")
    
    except Exception as e:
        st.error(f"❌ 删除操作失败: {e}")
        logger.error(f"删除分析记录失败: {analysis_id}, 错误: {e}")


def get_depth_text(depth: Optional[int]) -> str:
    """获取研究深度的文本描述"""
    depth_map = {
        1: "快速分析",
        2: "标准分析", 
        3: "深度分析"
    }
    return depth_map.get(depth, "未知")


if __name__ == "__main__":
    render_analysis_history()