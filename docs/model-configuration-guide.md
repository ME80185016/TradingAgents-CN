# 🧠 模型配置指南

本指南详细说明如何在TradingAgents-CN项目中添加新的AI模型版本和提供商。

## 📋 目录

1. [当前支持的模型](#当前支持的模型)
2. [添加新模型的方法](#添加新模型的方法)
3. [添加新提供商](#添加新提供商)
4. [配置文件说明](#配置文件说明)
5. [常见问题](#常见问题)

## 当前支持的模型

### 🇨🇳 阿里百炼 (DashScope)
- `qwen-turbo` - 快速响应
- `qwen-plus-latest` - 平衡性能
- `qwen-max` - 最强性能
- `qwen-long` - 长文本处理
- `qwen-vl-plus` - 视觉理解
- `qwen-vl-max` - 高级视觉
- `qwen-math-plus` - 数学专用
- `qwen-coder-plus` - 代码专用

### 🚀 DeepSeek
- `deepseek-chat` - 通用对话模型
- `deepseek-coder` - 代码专用模型
- `deepseek-reasoner` - 推理专用模型
- `deepseek-r1` - 最新推理模型
- `deepseek-r1-lite-preview` - 轻量推理模型

### 🌟 Google AI
- `gemini-2.5-pro` - 最新旗舰模型
- `gemini-2.5-flash` - 最新快速模型
- `gemini-2.5-flash-lite` - 轻量快速
- `gemini-2.0-flash` - 推荐使用
- `gemini-1.5-pro` - 强大性能
- `gemini-1.5-flash` - 快速响应
- `gemini-pro-vision` - 视觉理解专用

### 🤖 OpenAI
- `o1` - 最新推理模型
- `o1-pro` - 专业推理模型
- `o1-mini` - 轻量推理模型
- `gpt-4o` - 最新旗舰模型
- `gpt-4o-mini` - 轻量旗舰
- `gpt-4-turbo` - 强化版
- `gpt-4o-2024-11-20` - 最新版本

### 🌐 OpenRouter (支持最多模型)
- **OpenAI系列**: o4, o3, o1, GPT-4o等
- **Anthropic系列**: Claude 4, Claude 3.5等
- **Meta系列**: Llama 4, Llama 3.3等
- **Google系列**: Gemini 2.5, Gemma 3等

### 🇨🇳 硅基流动 (SiliconFlow)
- Qwen3系列思维链模型
- DeepSeek-R1
- GLM-4.5
- Kimi-K2

## 添加新模型的方法

### 方法1: 使用OpenRouter（最推荐）

这是最简单的方法，无需修改代码：

1. **获取OpenRouter API密钥**:
   ```bash
   # 在.env文件中添加
   OPENROUTER_API_KEY=your_openrouter_key
   ```

2. **在Web界面中选择**:
   - 提供商选择: "OpenRouter"
   - 模型类别选择: "自定义模型"
   - 输入任意OpenRouter支持的模型ID

3. **支持的模型格式**:
   ```
   anthropic/claude-3.7-sonnet
   openai/o4-mini-high
   meta-llama/llama-4-maverick
   google/gemini-2.5-pro
   ```

### 方法2: 使用自定义OpenAI端点

适用于OpenAI兼容的API服务：

1. **在Web界面选择**:
   - 提供商: "自定义OpenAI端点"
   - API端点URL: `https://your-api-endpoint.com/v1`
   - API密钥: 相应的密钥
   - 模型名称: 自定义或选择预设

2. **常用端点示例**:
   ```
   OpenAI官方: https://api.openai.com/v1
   本地部署: http://localhost:8000/v1
   中转服务: https://api.openai-proxy.com/v1
   ```

### 方法3: 修改代码添加模型

如果您想为特定提供商添加更多预设模型：

#### 1. 编辑sidebar.py文件

文件位置: `web/components/sidebar.py`

#### 2. 找到对应提供商的配置部分

例如，为阿里百炼添加新模型：

```python
# 找到这一行（约第242行）
dashscope_options = ["qwen-turbo", "qwen-plus-latest", "qwen-max"]

# 修改为
dashscope_options = [
    "qwen-turbo", 
    "qwen-plus-latest", 
    "qwen-max",
    "qwen-your-new-model"  # 添加新模型
]
```

#### 3. 更新显示名称映射

```python
# 找到format_func部分
format_func=lambda x: {
    "qwen-turbo": "Turbo - 快速响应",
    "qwen-plus-latest": "Plus - 平衡性能",
    "qwen-max": "Max - 最强性能",
    "qwen-your-new-model": "您的新模型 - 描述"  # 添加新模型描述
}[x],
```

## 添加新提供商

如果您想添加全新的AI提供商（如百度、智谱等），需要以下步骤：

### 1. 修改sidebar.py

在提供商选择列表中添加新选项：

```python
# 找到llm_provider选择部分（约第207行）
llm_provider = st.selectbox(
    "LLM提供商",
    options=["dashscope", "deepseek", "google", "openai", "openrouter", "siliconflow", "custom_openai", "your_new_provider"],
    # ...
)
```

### 2. 添加新提供商的模型配置

```python
elif llm_provider == "your_new_provider":
    your_provider_options = [
        "model-1",
        "model-2", 
        "model-3"
    ]
    
    llm_model = st.selectbox(
        "选择模型",
        options=your_provider_options,
        format_func=lambda x: {
            "model-1": "模型1 - 描述",
            "model-2": "模型2 - 描述", 
            "model-3": "模型3 - 描述"
        }[x],
        help="选择您的提供商模型",
        key="your_provider_model_select"
    )
```

### 3. 在trading_graph.py中添加支持

文件位置: `tradingagents/graph/trading_graph.py`

在`__init__`方法中添加新提供商的LLM初始化逻辑：

```python
elif self.config["llm_provider"] == "your_new_provider":
    # 初始化您的提供商的LLM
    your_api_key = os.getenv('YOUR_PROVIDER_API_KEY')
    if not your_api_key:
        raise ValueError("需要设置YOUR_PROVIDER_API_KEY环境变量")
    
    # 创建LLM实例
    self.deep_thinking_llm = YourProviderLLM(
        model=self.config["deep_think_llm"],
        api_key=your_api_key,
        temperature=0.1,
        max_tokens=2000
    )
    # ...
```

### 4. 创建适配器（如需要）

如果新提供商不兼容OpenAI格式，需要创建适配器：

```python
# 创建文件: tradingagents/llm_adapters/your_provider_adapter.py
from langchain.chat_models.base import BaseChatModel

class YourProviderLLM(BaseChatModel):
    def __init__(self, model, api_key, **kwargs):
        # 实现您的提供商LLM适配器
        pass
```

## 配置文件说明

### 环境变量配置 (.env)

```bash
# 基础提供商
DASHSCOPE_API_KEY=your_dashscope_key
DEEPSEEK_API_KEY=your_deepseek_key  
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key

# 聚合服务
OPENROUTER_API_KEY=your_openrouter_key
SILICONFLOW_API_KEY=your_siliconflow_key

# 自定义端点
CUSTOM_OPENAI_API_KEY=your_custom_key
CUSTOM_OPENAI_BASE_URL=https://your-endpoint.com/v1

# 新提供商
YOUR_PROVIDER_API_KEY=your_new_provider_key
```

### 模型映射配置

在`tradingagents/llm_adapters/openai_compatible_base.py`中维护OpenAI兼容提供商的模型配置：

```python
OPENAI_COMPATIBLE_PROVIDERS = {
    "your_provider": {
        "adapter_class": YourProviderAdapter,
        "base_url": "https://api.yourprovider.com/v1",
        "api_key_env": "YOUR_PROVIDER_API_KEY",
        "models": {
            "model-name": {
                "context_length": 32768, 
                "supports_function_calling": True
            }
        }
    }
}
```

## 常见问题

### Q: 添加的模型不显示怎么办？

A: 检查以下几点：
1. 是否正确修改了`sidebar.py`中的选项列表
2. 是否更新了`format_func`中的显示名称映射
3. 重启Web应用: `Ctrl+C` 然后重新运行

### Q: 模型调用失败怎么办？

A: 确认以下配置：
1. API密钥是否正确配置
2. 模型名称是否与提供商文档一致
3. 是否在`trading_graph.py`中添加了相应的初始化逻辑

### Q: 如何测试新添加的模型？

A: 在Web界面中：
1. 选择新的提供商和模型
2. 输入简单的股票代码（如AAPL）
3. 点击"开始分析"测试模型响应

### Q: 支持哪些OpenAI兼容的服务？

A: 理论上支持所有OpenAI API格式的服务，包括：
- OpenAI官方API
- Azure OpenAI
- 各种OpenAI代理服务
- 本地部署的兼容服务（如Ollama、vLLM等）
- 国内中转服务

## 🎯 推荐配置

### 初学者推荐
- **提供商**: 阿里百炼 (DashScope)
- **模型**: qwen-plus-latest
- **优点**: 中文友好，性价比高，配置简单

### 高级用户推荐  
- **提供商**: OpenRouter
- **模型类别**: 自定义模型
- **模型**: anthropic/claude-3.5-sonnet
- **优点**: 支持所有主流模型，切换方便

### 本地部署推荐
- **提供商**: 自定义OpenAI端点
- **端点**: http://localhost:8000/v1
- **优点**: 数据隐私，成本可控

## 📚 参考资源

- [OpenRouter模型列表](https://openrouter.ai/models)
- [阿里百炼文档](https://help.aliyun.com/zh/dashscope/)
- [DeepSeek API文档](https://platform.deepseek.com/api-docs/)
- [Google AI Studio](https://aistudio.google.com/)
- [OpenAI模型文档](https://platform.openai.com/docs/models)

---

💡 **提示**: 如果您需要添加特定的模型或遇到配置问题，请查看项目的GitHub Issues或提交新的Issue。