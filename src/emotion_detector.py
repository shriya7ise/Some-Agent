import logging
import redis
import yaml
import torch
from transformers import pipeline
from retry import retry
import spacy
from utils.utils import logger, config_path
import os

config_path = os.path.abspath(config_path)

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

redis_client = redis.Redis(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["db"]
)

# Determine device (use GPU if available, else CPU)
device = 0 if torch.cuda.is_available() else -1

nlp = pipeline(
    "text-classification",
    model=config["api"]["huggingface"]["model"],
    tokenizer=config["api"]["huggingface"]["model"],
    top_k=None,
    device=device 
)
spacy_nlp = spacy.load("en_core_web_sm")

@retry(tries=config["api"]["huggingface"]["retry_attempts"], delay=1, backoff=2)
def detect_emotion(text: str) -> tuple[str, float, list[tuple[str, str]]]:
    cache_key = f"emotion:{text}"
    cached = redis_client.get(cache_key)
    if cached:
        emotion, confidence = cached.decode().split(":")
        return emotion, float(confidence), []

    try:
        doc = spacy_nlp(text)
        entities = [(ent.label_, ent.text) for ent in doc.ents]
        results = nlp(text)
        top_emotion = max(results[0], key=lambda x: x["score"])
        emotion = top_emotion["label"]
        confidence = top_emotion["score"]

        redis_client.setex(
            cache_key,
            config["redis"]["cache_ttl_minutes"] * 60,
            f"{emotion}:{confidence}"
        )
        return emotion, confidence, entities
    except Exception as e:
        logger.error(f"Emotion detection error: {str(e)}")
        return config["api"]["huggingface"]["fallback_emotion"], 0.0, []