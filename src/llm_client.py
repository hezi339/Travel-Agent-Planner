"""
LLM 客户端模块
职责：统一管理大语言模型的配置与初始化，避免在 Agent / Web 中重复写密钥逻辑。
"""

from pathlib import Path

from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

# 始终从项目根目录加载 .env（不依赖终端当前在哪个文件夹）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# 智谱 AI 开放平台（OpenAI 兼容接口）
# 文档：https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
# 默认模型 GLM-5.2，可在 .env 中通过 ZHIPU_MODEL 覆盖
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-5.2")


def get_api_key() -> str:
    """读取智谱 AI API 密钥，缺失时抛出明确错误。"""
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError(
            f"未配置 ZHIPU_API_KEY，请在 {PROJECT_ROOT / '.env'} 中填写智谱 API Key"
        )
    return api_key


def create_llm():
    """
    创建并返回 LangChain ChatOpenAI 实例（对接智谱 AI GLM 系列）。
    temperature=0 让输出更稳定，便于 Agent 按 <action> 格式调用工具。
    """
    llm = ChatOpenAI(
        model=ZHIPU_MODEL,
        temperature=0,
        openai_api_key=get_api_key(),
        base_url=ZHIPU_BASE_URL,
    )
    return llm
