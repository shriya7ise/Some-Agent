import yaml
import redis
from langgraph.graph import StateGraph
from src.agent_state import AgentState
from src.emotion_detector import detect_emotion
from src.script_responder import get_response
from utils.utils import get_db_connection, logger, config_path
import sys
import os

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

redis_client = redis.Redis(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["db"]
)

def emotion_node(state: AgentState) -> AgentState:
    emotion, confidence, entities = detect_emotion(state["user_message"])
    state["emotion"] = emotion
    state["emotion_confidence"] = confidence
    state["entities"] = entities

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for entity_type, entity_value in entities:
                cur.execute(
                    """
                    INSERT INTO user_preferences (user_id, preference_key, preference_value, entity_type, entity_value, frequency)
                    VALUES (%s, %s, %s, %s, %s, %d)
                    ON CONFLICT (user_id, preference_key)
                    DO UPDATE SET
                        frequency = user_preferences.frequency + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    """,
                    (state["user_id"], f"{entity_type}:{entity_value}", entity_value, entity_type, entity_value, 1)
                )
            conn.commit()
    return state

def memory_node(state: AgentState) -> AgentState:
    memory_key = f"{config['memory']['memory_module']['redis_prefix']}{state['user_id']}"
    recent_memories = redis_client.lrange(memory_key, 0, config['memory']['routing_agent']['context_window'] - 1)
    state["recent_memories"] = [m.decode().split(":")[1:] for m in recent_memories]  # [emotion, strategy]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT entity_type, entity_value, frequency, last_accessed
                FROM user_preferences
                WHERE user_id = %s AND entity_type IS NOT NULL
                ORDER BY last_accessed DESC, frequency DESC
                LIMIT %s
                """,
                (state["user_id"], config['memory']['knowledge_graph']['max_entities_per_user'])
            )
            state["entities_from_graph"] = cur.fetchall()
    return state

async def response_node(state: AgentState) -> AgentState:
    response, strategy = await get_response(
        state["user_message"],
        state["user_id"],
        state["emotion"]
    )
    state["response"] = response
    state["strategy"] = strategy
    state["output"] = response

    memory_key = f"{config['memory']['memory_module']['redis_prefix']}{state['user_id']}"
    redis_client.lpush(memory_key, f"{state['chat_id']}:{state['emotion']}:{strategy}")
    redis_client.ltrim(memory_key, 0, config['memory']['memory_module']['max_memories_per_user'] - 1)
    redis_client.expire(memory_key, config['memory']['knowledge_graph']['entity_ttl_days'] * 86400)
    return state

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("emotion", emotion_node)
    graph.add_node("memory", memory_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("emotion")
    graph.add_edge("emotion", "memory")
    graph.add_edge("memory", "response")
    graph.set_finish_point("response")

    return graph.compile()