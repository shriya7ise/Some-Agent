import redis
import yaml
import numpy as np
from utils.utils import logger, config_path
import os


with open(config_path, "r") as f:
    config = yaml.safe_load(f)

redis_client = redis.Redis(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["db"]
)

def get_rl_strategy(feedback: str, recent_emotions: list = []) -> str:
    arms = config["rl"]["arms"]
    memory_key = f"{config['memory']['memory_module']['redis_prefix']}strategy"

    # Initialize bandit parameters
    for arm in arms:
        alpha_key = f"bandit:alpha:{arm}"
        beta_key = f"bandit:beta:{arm}"
        if not redis_client.exists(alpha_key):
            redis_client.set(alpha_key, 1)
            redis_client.set(beta_key, 1)

    # Incorporate memory context
    emotion_counts = {e: recent_emotions.count(e) for e in set(recent_emotions)}
    scores = {}
    for arm in arms:
        alpha = float(redis_client.get(f"bandit:alpha:{arm}") or 1)
        beta = float(redis_client.get(f"bandit:beta:{arm}") or 1)
        base_score = np.random.beta(alpha, beta)
        memory_boost = sum(
            config["memory"]["memory_module"]["frequency_weight"] * emotion_counts.get(e, 0)
            for e in emotion_counts
        )
        scores[arm] = base_score + memory_boost * config["memory"]["memory_module"]["recency_weight"]

    selected_arm = max(scores, key=scores.get)
    redis_client.lpush(memory_key, f"{selected_arm}:{feedback}")
    redis_client.ltrim(memory_key, 0, config['memory']['memory_module']['max_memories_per_user'] - 1)
    return selected_arm