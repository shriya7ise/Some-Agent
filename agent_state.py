from typing import TypedDict, List

class AgentState(TypedDict):
    input: str
    emotion: str
    emotion_confidence: float
    chat_history: List[dict]
    persuasion_prompt: str
    output: str