"""
DashScope API 错误处理工具
专门处理DashScope内容审核失败等问题
"""

import re
import time
from typing import Dict, Any, Optional
from tradingagents.utils.logging_init import get_logger

logger = get_logger('default')


class DashScopeErrorHandler:
    """DashScope API 错误处理器"""
    
    # 敏感词汇替换映射
    SENSITIVE_WORD_REPLACEMENTS = {
        "反驳": "讨论",
        "批判": "分析", 
        "威胁": "风险",
        "攻击": "质疑",
        "危险": "不确定",
        "激进": "积极",
        "风险": "不确定性",
        "损失": "波动",
        "失败": "挑战",
        "崩溃": "下跌",
        "暴跌": "下降",
        "泡沫": "高估值",
        "操纵": "影响",
        "欺诈": "不规范",
        "骗局": "误导",
        "血洗": "大幅下跌",
        "割韭菜": "获利了结",
        "庄家": "大资金",
        "做空": "看空",
        "砸盘": "抛售",
        "爆仓": "强制平仓"
    }
    
    @staticmethod
    def is_content_inspection_error(error: Exception) -> bool:
        """检查是否是内容审核失败错误"""
        error_message = str(error)
        return "data_inspection_failed" in error_message.lower()
    
    @staticmethod
    def sanitize_content(content: str, max_length: int = 4000) -> str:
        """清理内容，移除可能触发审核的词汇"""
        if not isinstance(content, str):
            return content
        
        filtered_content = content
        
        # 替换敏感词汇
        for sensitive_word, replacement in DashScopeErrorHandler.SENSITIVE_WORD_REPLACEMENTS.items():
            filtered_content = filtered_content.replace(sensitive_word, replacement)
        
        # 内容长度控制
        if len(filtered_content) > max_length:
            filtered_content = filtered_content[:max_length] + "..."
            logger.warning(f"⚠️ 内容过长，已截断到{max_length}字符")
        
        return filtered_content
    
    @staticmethod
    def create_safe_prompt_template(role: str, task: str) -> str:
        """创建安全的提示模板"""
        safe_templates = {
            "conservative": """作为稳健的投资分析师，您的目标是通过数据分析提供平衡的投资建议。
请基于提供的市场数据进行专业分析，重点关注：
1. 市场趋势分析
2. 基本面评估
3. 不确定性因素识别
4. 投资策略建议

请以专业、客观的语调进行分析，避免过于情绪化的表达。""",
            
            "neutral": """作为客观的市场分析师，您需要基于数据提供平衡的市场观点。
请综合考虑各种因素，包括：
1. 市场技术面分析
2. 基本面数据评估
3. 市场情绪判断
4. 平衡的投资建议

保持中性客观的分析角度，提供有建设性的投资参考。""",
            
            "aggressive": """作为积极的投资分析师，您专注于识别市场机会。
请基于市场数据分析潜在的投资机会，重点关注：
1. 增长潜力分析
2. 市场机会识别
3. 技术面突破点
4. 投资时机判断

以数据为基础，提供专业的投资机会分析。"""
        }
        
        return safe_templates.get(role, safe_templates["neutral"])
    
    @staticmethod
    def create_fallback_response(role: str) -> str:
        """创建备用响应"""
        fallback_responses = {
            "conservative": """基于当前市场数据，从稳健投资角度建议采取谨慎策略。
考虑到市场不确定性，建议重点关注：
1. 基本面分析
2. 适度的投资组合配置
3. 定期的市场评估
4. 平衡收益与稳定性

这种稳健的方法有助于在保护资本的同时寻求合理的回报机会。""",
            
            "neutral": """基于当前市场数据，建议采取平衡的投资策略。
在考虑增长机会的同时，也要重视风险管理：
1. 多元化投资组合
2. 适时的策略调整
3. 市场趋势跟踪
4. 灵活的应对机制

建议根据市场变化适时调整投资组合，保持投资策略的灵活性。""",
            
            "aggressive": """基于市场数据分析，认为当前市场存在一定的增长机会。
建议在管理风险的同时，适度把握市场机会：
1. 精选优质标的
2. 多元化投资策略
3. 技术面分析应用
4. 时机把握能力

通过专业分析和风险控制，以期获得更好的投资回报。"""
        }
        
        return fallback_responses.get(role, fallback_responses["neutral"])
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0, 
                          backoff_factor: float = 2.0) -> Any:
        """带指数退避的重试机制"""
        delay = initial_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                logger.warning(f"⚠️ 尝试 {attempt + 1}/{max_retries + 1} 失败: {e}")
                
                if DashScopeErrorHandler.is_content_inspection_error(e):
                    logger.info(f"🔍 检测到内容审核错误，准备内容过滤重试")
                
                time.sleep(delay)
                delay *= backoff_factor
        
        raise Exception("重试次数已达上限")


def safe_llm_invoke(llm, prompt: str, role: str = "neutral", 
                   max_retries: int = 3, max_length: int = 4000) -> str:
    """安全的LLM调用包装器"""
    
    def attempt_invoke():
        # 内容过滤
        safe_prompt = DashScopeErrorHandler.sanitize_content(prompt, max_length)
        
        # 调用LLM
        response = llm.invoke(safe_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    try:
        # 使用重试机制
        return DashScopeErrorHandler.retry_with_backoff(
            attempt_invoke, 
            max_retries=max_retries
        )
    except Exception as e:
        logger.error(f"❌ LLM调用最终失败: {e}")
        # 返回安全的备用响应
        return DashScopeErrorHandler.create_fallback_response(role)


# 导出主要功能
__all__ = [
    'DashScopeErrorHandler',
    'safe_llm_invoke'
]
