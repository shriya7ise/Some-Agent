from langgraph.graph import StateGraph
from agent_state import AgentState
from emotion_detector import detect_emotion
from script_responder import script_response

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("detect_emotion", detect_emotion)
    workflow.add_node("script_response", script_response)
    workflow.add_edge("detect_emotion", "script_response")
    workflow.set_entry_point("detect_emotion")
    return workflow.compile()