import json
import os

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI


with open(os.path.join("config", "models.json"), "r", encoding="utf-8") as f:
    MODELS = json.load(f)

active_profile = MODELS["active_profile"]
profile_config = MODELS["profiles"][active_profile]


def create_llm(profile_name: str, model_name: str, api_key: str, temperature: float = 0.3):
    if not api_key:
        raise ValueError(f"{profile_name} 的 api_key 为空")

    if profile_name == "qwen":
        return ChatTongyi(
            model_name=model_name,
            temperature=temperature,
            dashscope_api_key=api_key,
        )
    elif profile_name == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported profile: {profile_name}")


main_llm = create_llm(
    active_profile,
    profile_config["main_llm"],
    profile_config["api_key"],
    temperature=0.3,
)

fast_llm = create_llm(
    active_profile,
    profile_config["fast_llm"],
    profile_config["api_key"],
    temperature=0.1,
)

reference_llm = create_llm(
    active_profile,
    profile_config["reference_llm"],
    profile_config["api_key"],
    temperature=0.0,
)