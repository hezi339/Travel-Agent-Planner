"""
ReAct 输出解析器
职责：从 LLM 原始文本中提取 <thought>、<action>、<final_answer> 标签内容。
"""

import re
import shlex


def _split_tool_args(arg_str: str) -> list[str]:
    """
    解析工具参数字符串。
    中文场景下不用 shlex（会把「广州,」拆成带逗号的城市名），优先按逗号分割。
    """
    arg_str = arg_str.strip()
    if not arg_str:
        return []

    # 含中文时直接按逗号切分，避免 shlex 解析错误
    if re.search(r"[\u4e00-\u9fff]", arg_str):
        return [
            part.strip().strip("'\"")
            for part in arg_str.split(",")
            if part.strip()
        ]

    try:
        return shlex.split(arg_str)
    except Exception:
        return [
            part.strip().strip("'\"")
            for part in arg_str.split(",")
            if part.strip()
        ]


def parse_action(response_content: str):
    """
    解析 LLM 输出，返回三种类型之一：
    - action：需要调用工具
    - final_answer：推理结束，输出最终方案
    - unknown：格式不符合约定，Agent 应终止
    """
    thought_match = re.search(r"<thought>(.*?)</thought>", response_content, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    action_match = re.search(r"<action>(.*?)</action>", response_content, re.DOTALL)
    if action_match:
        action_content = action_match.group(1).strip()
        tool_match = re.match(r"([a-zA-Z_]+)\((.*?)\)", action_content, re.DOTALL)
        if tool_match:
            tool_name = tool_match.group(1)
            arg_str = tool_match.group(2)
            return {
                "type": "action",
                "thought": thought,
                "tool_name": tool_name,
                "tool_args": _split_tool_args(arg_str),
            }

    ans_match = re.search(r"<final_answer>(.*?)</final_answer>", response_content, re.DOTALL)
    if ans_match:
        return {
            "type": "final_answer",
            "thought": thought,
            "content": ans_match.group(1).strip(),
        }

    return {"type": "unknown", "thought": thought}
