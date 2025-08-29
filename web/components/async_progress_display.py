#!/usr/bin/env python3
"""
异步进度显示组件
支持定时刷新，从Redis或文件获取进度状态
"""

import streamlit as st
import time
from typing import Optional, Dict, Any
from web.utils.async_progress_tracker import get_progress_by_id, format_time

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('async_display')

class AsyncProgressDisplay:
    """异步进度显示组件"""
    
    def __init__(self, container, analysis_id: str, refresh_interval: float = 1.0):
        self.container = container
        self.analysis_id = analysis_id
        self.refresh_interval = refresh_interval
        
        # 添加DOM操作锁，防止重复操作
        self.dom_lock = False
        
        # 创建显示组件时使用锁保护
        if not self.dom_lock:
            self.dom_lock = True
            try:
                with self.container:
                    self.progress_bar = st.progress(0)
                    self.status_text = st.empty()
                    self.step_info = st.empty()
                    self.time_info = st.empty()
                    self.refresh_button = st.empty()
            finally:
                self.dom_lock = False
        
        # 初始化状态
        self.last_update = 0
        self.is_completed = False
        
        logger.info(f"📊 [异步显示] 初始化: {analysis_id}, 刷新间隔: {refresh_interval}s")
    
    def update_display(self) -> bool:
        """更新显示，返回是否需要继续刷新"""
        current_time = time.time()
        
        # 如果DOM操作正在进行，跳过此次更新
        if self.dom_lock:
            return not self.is_completed
        
        # 检查是否需要刷新
        if current_time - self.last_update < self.refresh_interval and not self.is_completed:
            return not self.is_completed
        
        # 获取进度数据
        progress_data = get_progress_by_id(self.analysis_id)
        
        if not progress_data:
            try:
                self.status_text.error("❌ 无法获取分析进度，请检查分析是否正在运行")
            except Exception as e:
                logger.error(f"📊 [DOM错误] 状态文本更新失败: {e}")
            return False
        
        # 更新显示
        self._render_progress(progress_data)
        self.last_update = current_time
        
        # 检查是否完成
        status = progress_data.get('status', 'running')
        self.is_completed = status in ['completed', 'failed']
        
        return not self.is_completed
    
    def _render_progress(self, progress_data: Dict[str, Any]):
        """渲染进度显示"""
        try:
            # 基本信息
            current_step = progress_data.get('current_step', 0)
            total_steps = progress_data.get('total_steps', 8)
            progress_percentage = progress_data.get('progress_percentage', 0.0)
            status = progress_data.get('status', 'running')
            
            # 更新进度条
            self.progress_bar.progress(min(progress_percentage / 100, 1.0))
            
            # 状态信息
            step_name = progress_data.get('current_step_name', '未知')
            step_description = progress_data.get('current_step_description', '')
            last_message = progress_data.get('last_message', '')
            
            # 状态图标
            status_icon = {
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '🔄')
            
            # 显示当前状态
            self.status_text.info(f"{status_icon} **当前状态**: {last_message}")
            
            # 显示步骤信息
            if status == 'failed':
                self.step_info.error(f"❌ **分析失败**: {last_message}")
            elif status == 'completed':
                self.step_info.success(f"🎉 **分析完成**: 所有步骤已完成")

                # 添加查看报告按钮
                with self.step_info:
                    if st.button("📊 查看分析报告", key=f"view_report_{progress_data.get('analysis_id', 'unknown')}", type="primary"):
                        analysis_id = progress_data.get('analysis_id')
                        # 尝试恢复分析结果（如果还没有的话）
                        if not st.session_state.get('analysis_results'):
                            try:
                                from web.utils.analysis_runner import format_analysis_results
                                raw_results = progress_data.get('raw_results')
                                if raw_results:
                                    formatted_results = format_analysis_results(raw_results)
                                    if formatted_results:
                                        st.session_state.analysis_results = formatted_results
                                        st.session_state.analysis_running = False
                            except Exception as e:
                                st.error(f"恢复分析结果失败: {e}")

                        # 触发显示报告
                        st.session_state.show_analysis_results = True
                        st.session_state.current_analysis_id = analysis_id
                        st.rerun()
            else:
                self.step_info.info(f"📊 **进度**: 第 {current_step + 1} 步，共 {total_steps} 步 ({progress_percentage:.1f}%)\n\n"
                                  f"**当前步骤**: {step_name}\n\n"
                                  f"**步骤说明**: {step_description}")
            
            # 时间信息 - 实时计算已用时间
            start_time = progress_data.get('start_time', 0)
            estimated_total_time = progress_data.get('estimated_total_time', 0)

            # 计算已用时间
            import time
            if status == 'completed':
                # 已完成的分析使用存储的最终耗时
                real_elapsed_time = progress_data.get('elapsed_time', 0)
            elif start_time > 0:
                # 进行中的分析使用实时计算
                real_elapsed_time = time.time() - start_time
            else:
                # 备用方案
                real_elapsed_time = progress_data.get('elapsed_time', 0)

            # 重新计算剩余时间
            remaining_time = max(estimated_total_time - real_elapsed_time, 0)
            
            if status == 'completed':
                self.time_info.success(f"⏱️ **已用时间**: {format_time(real_elapsed_time)} | **总耗时**: {format_time(real_elapsed_time)}")
            elif status == 'failed':
                self.time_info.error(f"⏱️ **已用时间**: {format_time(real_elapsed_time)} | **分析中断**")
            else:
                self.time_info.info(f"⏱️ **已用时间**: {format_time(real_elapsed_time)} | **预计剩余**: {format_time(remaining_time)}")
            
            # 刷新按钮（仅在运行时显示）- 添加异常保护
            try:
                if status == 'running':
                    with self.refresh_button:
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            if st.button("🔄 手动刷新", key=f"refresh_{self.analysis_id}"):
                                st.rerun()
                else:
                    self.refresh_button.empty()
            except Exception as e:
                logger.warning(f"📊 [DOM保护] 刷新按钮更新跳过: {e}")
                
        except Exception as e:
            logger.error(f"📊 [异步显示] 渲染失败: {e}")
            try:
                self.status_text.error(f"❌ 显示更新失败: {str(e)}")
            except:
                # 如果连错误显示都失败，只记录日志
                logger.error(f"📊 [DOM严重错误] 无法显示错误信息: {e}")
        finally:
            # 确保释放DOM锁
            self.dom_lock = False

def create_async_progress_display(container, analysis_id: str, refresh_interval: float = 1.0) -> AsyncProgressDisplay:
    """创建异步进度显示组件"""
    return AsyncProgressDisplay(container, analysis_id, refresh_interval)

def auto_refresh_progress(display: AsyncProgressDisplay, max_duration: float = 1800):
    """自动刷新进度显示"""
    start_time = time.time()
    
    # 使用Streamlit的自动刷新机制
    placeholder = st.empty()
    
    while True:
        # 检查超时
        if time.time() - start_time > max_duration:
            with placeholder:
                st.warning("⚠️ 分析时间过长，已停止自动刷新。请手动刷新页面查看最新状态。")
            break
        
        # 更新显示
        should_continue = display.update_display()
        
        if not should_continue:
            # 分析完成或失败，停止刷新
            break
        
        # 等待刷新间隔
        time.sleep(display.refresh_interval)
    
    logger.info(f"📊 [异步显示] 自动刷新结束: {display.analysis_id}")


def display_unified_progress(analysis_id: str, show_refresh_controls: bool = True, show_view_report_button: bool = True) -> bool:
    """
    统一的进度显示函数，避免重复元素
    返回是否已完成
    """
    import streamlit as st

    # 简化逻辑：直接调用显示函数，通过参数控制是否显示刷新按钮
    # 调用方负责确保只在需要的地方传入show_refresh_controls=True
    return display_static_progress_with_controls(analysis_id, show_refresh_controls, show_view_report_button)


def display_static_progress_with_controls(analysis_id: str, show_refresh_controls: bool = True, show_view_report_button: bool = True) -> bool:
    """
    显示静态进度，可控制是否显示刷新控件和查看报告按钮
    """
    import streamlit as st
    from web.utils.async_progress_tracker import get_progress_by_id

    # 添加全局显示锁，防止同一个analysis_id的进度被重复显示
    display_lock_key = f"progress_display_lock_{analysis_id}"
    if st.session_state.get(display_lock_key, False):
        # 如果已经在显示，直接返回
        logger.debug(f"📊 [显示锁定] 跳过重复显示: {analysis_id}")
        return False
    
    # 设置显示锁
    st.session_state[display_lock_key] = True
    
    try:
        # 显示进度区域标题
        st.markdown("### 📊 分析进度")
        
        # 获取进度数据
        progress_data = get_progress_by_id(analysis_id)

        if not progress_data:
            # 如果没有进度数据，显示默认的准备状态
            st.info("🔄 **当前状态**: 准备开始分析...")
            
            # 设置默认状态为initializing
            status = 'initializing'

            # 如果需要显示刷新控件，仍然显示
            if show_refresh_controls:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 刷新进度", key=f"refresh_unified_default_{analysis_id}"):
                        st.rerun()
                with col2:
                    auto_refresh_key = f"auto_refresh_unified_default_{analysis_id}"
                    # 只使用session state管理，不设置默认值避免状态冲突
                    if auto_refresh_key not in st.session_state:
                        st.session_state[auto_refresh_key] = True  # 默认为True
                    auto_refresh = st.checkbox("🔄 自动刷新", key=auto_refresh_key)
                    if auto_refresh and status == 'running':  # 只在运行时自动刷新
                        import time
                        time.sleep(3)  # 等待3秒
                        st.rerun()
                    elif auto_refresh and status in ['completed', 'failed']:
                        # 分析完成后自动关闭自动刷新
                        st.session_state[auto_refresh_key] = False

            return False  # 返回False表示还未完成

        # 解析进度数据（修复字段名称匹配）
        status = progress_data.get('status', 'running')
        current_step = progress_data.get('current_step', 0)
        current_step_name = progress_data.get('current_step_name', '准备阶段')
        progress_percentage = progress_data.get('progress_percentage', 0.0)

        # 计算已用时间
        start_time = progress_data.get('start_time', 0)
        estimated_total_time = progress_data.get('estimated_total_time', 0)
        import time
        if status == 'completed':
            # 已完成的分析使用存储的最终耗时
            elapsed_time = progress_data.get('elapsed_time', 0)
        elif start_time > 0:
            # 进行中的分析使用实时计算
            elapsed_time = time.time() - start_time
        else:
            # 备用方案
            elapsed_time = progress_data.get('elapsed_time', 0)

        # 重新计算剩余时间
        remaining_time = max(estimated_total_time - elapsed_time, 0)
        current_step_description = progress_data.get('current_step_description', '初始化分析引擎')
        last_message = progress_data.get('last_message', '准备开始分析')

        # 显示当前步骤
        st.write(f"**当前步骤**: {current_step_name}")

        # 显示进度条和统计信息
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("进度", f"{progress_percentage:.1f}%")

        with col2:
            st.metric("已用时间", format_time(elapsed_time))

        with col3:
            if status == 'completed':
                st.metric("预计剩余", "已完成")
            elif status == 'failed':
                st.metric("预计剩余", "已中断")
            else:
                st.metric("预计剩余", format_time(remaining_time))

        # 显示进度条
        st.progress(min(progress_percentage / 100.0, 1.0))

        # 显示当前任务
        st.write(f"**当前任务**: {current_step_description}")

        # 显示当前状态
        status_icon = {
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(status, '🔄')

        if status == 'completed':
            st.success(f"{status_icon} **当前状态**: {last_message}")

            # 添加查看报告按钮（只有在允许显示时才显示）
            if show_view_report_button and st.button("📊 查看分析报告", key=f"view_report_unified_{analysis_id}", type="primary"):
                # 尝试恢复分析结果（如果还没有的话）
                if not st.session_state.get('analysis_results'):
                    try:
                        from web.utils.async_progress_tracker import get_progress_by_id
                        from web.utils.analysis_runner import format_analysis_results
                        progress_data = get_progress_by_id(analysis_id)
                        if progress_data and progress_data.get('raw_results'):
                            formatted_results = format_analysis_results(progress_data['raw_results'])
                            if formatted_results:
                                st.session_state.analysis_results = formatted_results
                                st.session_state.analysis_running = False
                    except Exception as e:
                        st.error(f"恢复分析结果失败: {e}")

                # 触发显示报告
                st.session_state.show_analysis_results = True
                st.session_state.current_analysis_id = analysis_id
                st.rerun()
        elif status == 'failed':
            st.error(f"{status_icon} **当前状态**: {last_message}")
        else:
            st.info(f"{status_icon} **当前状态**: {last_message}")

        # 显示刷新控制的条件：
        # 1. 需要显示刷新控件 AND
        # 2. (分析正在运行 OR 分析刚开始还没有状态)
        if show_refresh_controls and (status == 'running' or status == 'initializing'):
            # 添加DOM操作保护和快速分析模式保护
            try:
                # 防止重复刷新的保护机制
                refresh_protection_key = f"refresh_protection_{analysis_id}"
                last_refresh_time = st.session_state.get(refresh_protection_key, 0)
                current_time = time.time()
                
                # 快速分析模式（研究深度为1）增加保护间隔
                research_depth = progress_data.get('steps', [{}])[0].get('research_depth', 2) if progress_data.get('steps') else 2
                protection_interval = 5 if research_depth == 1 else 2
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 刷新进度", key=f"refresh_unified_{analysis_id}"):
                        # 清除刷新保护，允许立即刷新
                        if refresh_protection_key in st.session_state:
                            del st.session_state[refresh_protection_key]
                        st.rerun()
                with col2:
                    auto_refresh_key = f"auto_refresh_unified_{analysis_id}"
                    # 只使用session state管理，不设置默认值避免状态冲突
                    if auto_refresh_key not in st.session_state:
                        st.session_state[auto_refresh_key] = True  # 默认为True，但快速分析模式降低刷新频率
                    auto_refresh = st.checkbox("🔄 自动刷新", key=auto_refresh_key)
                    
                    if auto_refresh and status == 'running':
                        # 检查刷新保护间隔
                        if current_time - last_refresh_time >= protection_interval:
                            # 更新刷新时间戳
                            st.session_state[refresh_protection_key] = current_time
                            # 针对快速分析模式，增加刷新间隔
                            sleep_time = 6 if research_depth == 1 else 3
                            time.sleep(sleep_time)
                            st.rerun()
                    elif auto_refresh and status in ['completed', 'failed']:
                        # 分析完成后自动关闭自动刷新
                        st.session_state[auto_refresh_key] = False
            except Exception as e:
                logger.warning(f"📊 [DOM保护] 刷新控件更新失败，跳过: {e}")

        # 不需要清理session state，因为我们通过参数控制显示

        return status in ['completed', 'failed']
        
    finally:
        # 无论成功还是失败，都要释放显示锁
        if display_lock_key in st.session_state:
            del st.session_state[display_lock_key]
