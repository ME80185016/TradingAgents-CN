#!/usr/bin/env python3
"""
TradingAgents-CN Web应用主入口
多智能体股票分析系统的Streamlit Web界面
"""

import streamlit as st
import sys
import os
from pathlib import Path
import threading
import uuid
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入页面组件
from web.components.header import render_header
from web.components.sidebar import render_sidebar
from web.components.analysis_form import render_analysis_form
from web.components.results_display import render_results
from web.components.async_progress_display import display_unified_progress
from web.utils.ui_utils import apply_hide_deploy_button_css, apply_common_styles

# 导入工具模块
from web.utils.analysis_runner import run_stock_analysis, format_analysis_results
from web.utils.async_progress_tracker import AsyncProgressTracker
from web.utils.thread_tracker import register_analysis_thread
from web.utils.file_session_manager import get_persistent_analysis_id, set_persistent_analysis_id

# 导入页面模块
from web.modules.analysis_history import render_analysis_history
from web.modules.token_statistics import render_token_statistics
from web.modules.config_management import render_config_management
from web.modules.cache_management import main as render_cache_management

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('web')


def setup_page_config():
    """配置页面基本设置"""
    st.set_page_config(
        page_title="TradingAgents-CN - 智能股票分析",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 应用通用样式
    apply_hide_deploy_button_css()
    apply_common_styles()


def initialize_session_state():
    """初始化session state"""
    # 分析状态
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'show_analysis_results' not in st.session_state:
        st.session_state.show_analysis_results = False
    if 'current_analysis_id' not in st.session_state:
        st.session_state.current_analysis_id = None
    
    # 模型配置（使用默认值）
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = "dashscope"
    if 'llm_model' not in st.session_state:
        st.session_state.llm_model = "qwen-plus"
    
    # 表单配置持久化
    if 'form_config' not in st.session_state:
        st.session_state.form_config = {}
    
    # 恢复持久化的分析状态
    try:
        persistent_id = get_persistent_analysis_id()
        if persistent_id and not st.session_state.current_analysis_id:
            st.session_state.current_analysis_id = persistent_id
            logger.info(f"📊 [会话恢复] 恢复分析ID: {persistent_id}")
    except Exception as e:
        logger.debug(f"📊 [会话恢复] 恢复失败: {e}")


def run_analysis_in_background(stock_symbol, analysis_date, analysts, research_depth, 
                               llm_provider, llm_model, market_type, analysis_id):
    """在后台线程中运行分析"""
    try:
        logger.info(f"🚀 [后台分析] 开始分析: {stock_symbol} ({analysis_id})")
        
        # 创建进度跟踪器
        tracker = AsyncProgressTracker(analysis_id, analysts, research_depth, llm_provider)
        
        # 创建进度回调函数
        def progress_callback(message, step=None, total_steps=None):
            try:
                tracker.update_progress(message, step)
            except Exception as e:
                logger.error(f"📊 [进度更新] 失败: {e}")
        
        # 执行分析
        results = run_stock_analysis(
            stock_symbol=stock_symbol,
            analysis_date=analysis_date,
            analysts=analysts,
            research_depth=research_depth,
            llm_provider=llm_provider,
            llm_model=llm_model,
            market_type=market_type,
            progress_callback=progress_callback
        )
        
        # 标记完成
        if results.get('success', False):
            tracker.mark_completed("✅ 分析成功完成！", results)
            logger.info(f"✅ [后台分析] 分析完成: {stock_symbol} ({analysis_id})")
        else:
            error_msg = results.get('error', '未知错误')
            tracker.mark_failed(error_msg)
            logger.error(f"❌ [后台分析] 分析失败: {stock_symbol} ({analysis_id}), 错误: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ [后台分析] 异常: {e}", exc_info=True)
        try:
            tracker.mark_failed(str(e))
        except:
            pass


def render_stock_analysis_page():
    """渲染股票分析主页面"""
    # 页面头部
    render_header()
    
    # 主内容区域 - 使用固定的2列布局，确保右侧指南始终可用
    col1, col2 = st.columns([2, 1])  # 固定2:1比例布局
    
    with col1:
        # 检查是否需要显示分析结果
        if st.session_state.get('show_analysis_results') and st.session_state.get('analysis_results'):
            st.header("📊 分析结果")
            render_results(st.session_state.analysis_results)
            
            # 添加返回按钮
            if st.button("🔙 返回分析", type="secondary"):
                st.session_state.show_analysis_results = False
                st.session_state.analysis_results = None
                st.rerun()
        else:
            # 显示分析表单和进度
            if not st.session_state.get('analysis_running'):
                # 显示分析表单
                form_data = render_analysis_form()
                
                # 检查表单是否成功提交并包含必要数据
                if form_data and form_data.get('submitted') and form_data.get('stock_symbol'):
                    # 生成分析ID
                    analysis_id = f"analysis_{uuid.uuid4().hex[:8]}_{int(time.time())}"
                    
                    # 保存表单配置
                    st.session_state.form_config = form_data
                    set_persistent_analysis_id(
                        analysis_id, "running", 
                        form_data['stock_symbol'], 
                        form_data['market_type'],
                        form_data
                    )
                    
                    # 设置分析状态
                    st.session_state.analysis_running = True
                    st.session_state.current_analysis_id = analysis_id
                    st.session_state.analysis_results = None
                    st.session_state.show_analysis_results = False
                    
                    # 从sidebar获取模型配置
                    llm_provider = st.session_state.get('llm_provider', 'dashscope')
                    llm_model = st.session_state.get('llm_model', 'qwen-plus')
                    
                    # 创建并启动后台分析线程
                    analysis_thread = threading.Thread(
                        target=run_analysis_in_background,
                        args=(
                            form_data['stock_symbol'],
                            form_data['analysis_date'], 
                            form_data['analysts'],
                            form_data['research_depth'],
                            llm_provider,
                            llm_model,
                            form_data['market_type'],
                            analysis_id
                        ),
                        name=f"Analysis-{analysis_id}",
                        daemon=True
                    )
                    
                    # 注册线程到跟踪器
                    register_analysis_thread(analysis_id, analysis_thread)
                    analysis_thread.start()
                    
                    logger.info(f"🚀 [分析启动] 后台线程已启动: {analysis_id}")
                    st.rerun()
            else:
                # 显示分析进度
                st.header("📊 分析进度")
                
                if st.session_state.current_analysis_id:
                    # 显示进度
                    is_completed = display_unified_progress(
                        st.session_state.current_analysis_id,
                        show_refresh_controls=True,
                        show_view_report_button=True
                    )
                    
                    if is_completed:
                        st.session_state.analysis_running = False
                        # 不自动重新运行，让用户手动刷新
                        
                    # 添加停止分析按钮
                    if st.button("⏹️ 停止分析", type="secondary"):
                        st.session_state.analysis_running = False
                        st.session_state.current_analysis_id = None
                        st.rerun()
                else:
                    st.error("❌ 分析ID丢失，请重新开始分析")
                    if st.button("🔄 重新开始"):
                        st.session_state.analysis_running = False
                        st.rerun()
    
    with col2:
        # 右侧使用指南 - 始终显示
        st.markdown("### 📋 使用指南")
        
        st.markdown("""
        **📊 分析功能说明**
        
        1. **股票代码**: 支持美股(AAPL)、A股(000001)、港股(0700.HK)
        2. **分析师选择**: 多维度专业分析
        3. **研究深度**: 1-5级，深度越高越详细
        4. **AI模型**: 支持多种大语言模型
        
        **🎯 分析流程**
        
        - 📋 数据验证和环境检查
        - 🔍 多智能体协同分析
        - 📊 综合结果整合
        - 📄 生成专业报告
        
        **⚡ 预估时间**
        
        - 快速分析: 2-5分钟
        - 标准分析: 5-10分钟  
        - 深度分析: 10-20分钟
        
        **📈 支持功能**
        
        - 实时进度跟踪
        - 历史记录查看
        - 报告导出下载
        - 成本使用统计
        """)
        
        # 显示系统状态
        st.markdown("---")
        st.markdown("### 🔧 系统状态")
        
        # 检查API配置状态
        import os
        dashscope_configured = bool(os.getenv("DASHSCOPE_API_KEY"))
        finnhub_configured = bool(os.getenv("FINNHUB_API_KEY"))
        
        st.markdown(f"**API配置状态:**")
        st.markdown(f"- 阿里百炼: {'✅ 已配置' if dashscope_configured else '❌ 未配置'}")
        st.markdown(f"- 金融数据: {'✅ 已配置' if finnhub_configured else '❌ 未配置'}")
        
        if not (dashscope_configured and finnhub_configured):
            st.warning("⚠️ 部分API未配置，可能影响分析功能")


def main():
    """主函数"""
    # 页面配置
    setup_page_config()
    
    # 初始化状态
    initialize_session_state()
    
    # 渲染侧边栏
    sidebar_config = render_sidebar()
    
    # 更新模型配置
    if sidebar_config:
        st.session_state.llm_provider = sidebar_config['llm_provider']
        st.session_state.llm_model = sidebar_config['llm_model']
    
    # 页面导航
    page_options = {
        "📊 股票分析": render_stock_analysis_page,
        "📈 历史记录": render_analysis_history,
        "💰 Token统计": render_token_statistics,
        "⚙️ 配置管理": render_config_management,
        "💾 缓存管理": render_cache_management
    }
    
    # 创建页面标签
    selected_page = st.selectbox(
        "选择功能页面",
        options=list(page_options.keys()),
        index=0,
        help="选择要使用的功能模块"
    )
    
    # 渲染选中的页面
    try:
        page_options[selected_page]()
    except Exception as e:
        st.error(f"❌ 页面加载失败: {e}")
        logger.error(f"页面加载失败: {selected_page}, 错误: {e}", exc_info=True)
        
        # 显示错误详情（仅在开发模式）
        if os.getenv("DEBUG", "false").lower() == "true":
            st.exception(e)


if __name__ == "__main__":
    main()