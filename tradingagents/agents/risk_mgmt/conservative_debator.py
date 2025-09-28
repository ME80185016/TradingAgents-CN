from langchain_core.messages import AIMessage
import time
import json

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")

# 导入安全调用工具
from tradingagents.utils.dashscope_error_handler import safe_llm_invoke


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""作为稳健的投资分析师，您的核心目标是保护资产价值、降低波动性，并追求稳定可持续的增长。您重视稳定性、安全性和不确定性管理，深入分析潜在的市场波动、经济周期变化和投资环境变化。在评估交易决策时，请仔细审查高不确定性因素，并提出更稳健的替代方案来确保长期回报。

交易决策详情：
{trader_decision}

请基于以下市场数据，与其他分析师进行专业讨论，重点关注稳健投资策略的价值：

市场研究数据：{market_research_report}
市场情绪分析：{sentiment_report}
市场资讯总结：{news_report}
基本面数据：{fundamentals_report}

当前讨论记录：{history}
积极分析师观点：{current_risky_response}
平衡分析师观点：{current_neutral_response}

请从稳健投资角度出发，与其他分析师进行建设性讨论。重点分析市场不确定性因素，提出平衡收益与稳定性的投资建议。通过数据分析展示稳健策略的长期价值，并针对其他观点进行专业探讨。

请以自然对话的方式用中文回应，保持专业分析师的语调，避免使用特殊格式。"""

        # 使用安全的LLM调用
        response_content = safe_llm_invoke(llm, prompt, role="conservative", max_retries=3)
        argument = f"Safe Analyst: {response_content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
