import os
import logging
import yaml
import uuid
from fastapi import FastAPI, Request, HTTPException
from celery import Celery
import redis
from utils import get_db_connection, validate_env_vars, logger
from emotion_detector import detect_emotion
from script_responder import get_response
from rl_learner import get_rl_strategy

app = FastAPI()
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

redis_client = redis.Redis(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["db"]
)

celery_app = Celery(
    "tasks",
    broker=f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}",
    backend=f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}"
)

@app.on_event("startup")
async def startup_event():
    validate_env_vars()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    user_message = data.get("message")
    if not user_id or not user_message:
        raise HTTPException(status_code=422, detail="Missing user_id or message")

    try:
        # Detect emotion and extract entities
        emotion, confidence, entities = detect_emotion(user_message)
        # Get response with memory context
        response, strategy = await get_response(user_message, user_id, emotion)
        chat_id = str(uuid.uuid4())

        # Save to interactions table
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO interactions (id, user_id, user_message, agent_response, emotion, emotion_confidence)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (chat_id, user_id, user_message, response, emotion, confidence)
                )
                # Save entities to user_preferences (Knowledge Graph)
                for entity_type, entity_value in entities:
                    cur.execute(
                        """
                        INSERT INTO user_preferences (user_id, preference_key, preference_value, entity_type, entity_value, frequency)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, preference_key)
                        DO UPDATE SET
                            frequency = user_preferences.frequency + 1,
                            last_accessed = CURRENT_TIMESTAMP
                        """,
                        (user_id, f"{entity_type}:{entity_value}", entity_value, entity_type, entity_value, 1)
                    )
                conn.commit()

        # Update Memory Module in Redis
        memory_key = f"{config['memory']['memory_module']['redis_prefix']}{user_id}"
        redis_client.lpush(memory_key, f"{chat_id}:{emotion}:{strategy}")
        redis_client.ltrim(memory_key, 0, config['memory']['memory_module']['max_memories_per_user'] - 1)
        redis_client.expire(memory_key, config['memory']['knowledge_graph']['entity_ttl_days'] * 86400)

        celery_app.send_task("process_interaction", args=[user_id, chat_id, response, strategy])
        return {"chat_id": chat_id, "response": response, "emotion": emotion, "strategy": strategy}
    except Exception as e:
        logger.error(f"Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def feedback(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    score = data.get("score")
    if not user_id or not chat_id or score is None:
        raise HTTPException(status_code=422, detail="Missing user_id, chat_id, or score")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE interactions
                    SET feedback_score = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (score, chat_id, user_id)
                )
                cur.execute(
                    """
                    INSERT INTO interaction_outcomes (user_id, chat_id, outcome, feedback_score)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, chat_id, get_rl_strategy(str(score)), score)
                )
                conn.commit()
        return {"status": "Feedback recorded"}
    except Exception as e:
        logger.error(f"Error in /feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))