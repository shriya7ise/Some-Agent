import os
import logging
import yaml
import redis
import aiohttp
from retry import retry
from rl_learner import get_rl_strategy
from utils import get_db_connection, logger

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

redis_client = redis.Redis(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["db"]
)

@retry(tries=config["api"]["grok"]["retry_attempts"], delay=1, backoff=2)
async def get_response(text: str, user_id: str, emotion: str) -> tuple[str, str]:
    cache_key = f"response:{text}:{emotion}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached.decode(), "cached"

    # Fetch memory context from Redis
    memory_key = f"{config['memory']['memory_module']['redis_prefix']}{user_id}"
    recent_memories = redis_client.lrange(memory_key, 0, config['memory']['routing_agent']['context_window'] - 1)
    context = [m.decode().split(":")[1:] for m in recent_memories]  # [emotion, strategy]

    # Fetch entities from PostgreSQL (Knowledge Graph)
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
                (user_id, config['memory']['knowledge_graph']['max_entities_per_user'])
            )
            entities = cur.fetchall()

    # Build context for routing
    entity_context = " ".join([f"{e['entity_type']}:{e['entity_value']}" for e in entities])
    recent_emotions = [c[0] for c in context]
    strategy = get_rl_strategy(emotion, recent_emotions)

    prompt = (
        f"{config['api']['huggingface']['base_persona']} "
        f"User emotion: {emotion}. "
        f"Context: {entity_context}. "
        f"Recent emotions: {', '.join(recent_emotions)}. "
        f"Use persuasive style: {config['api']['huggingface']['persuasive_styles'][emotion]}. "
        f"Message: {text}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            config["api"]["grok"]["url"],
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": config["api"]["grok"]["model"],
                "messages": [{"role": "user", "content": prompt}]
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                result = data["choices"][0]["message"]["content"]
                redis_client.setex(
                    cache_key,
                    config["redis"]["cache_ttl_minutes"] * 60,
                    result
                )
                return result, strategy
            else:
                logger.error(f"Grok API error: {await response.text()}")
                return config["api"]["grok"]["fallback_response"], "fallback"