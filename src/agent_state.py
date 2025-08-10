from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    user_message: str  # Renamed from 'input' for consistency
    emotion: str
    emotion_confidence: float
    chat_history: List[dict]
    persuasion_prompt: str
    response: str  # Renamed from 'output' for consistency
    user_id: str
    chat_id: str
    entities: Optional[List[tuple[str, str]]]
    entities_from_graph: Optional[List[dict]]
    recent_memories: Optional[List[list[str]]]