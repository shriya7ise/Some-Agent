from celery import Celery
from utils.utils import logger, config_path
import yaml

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

celery_app = Celery(
    "tasks",
    broker=f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}",
    backend=f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}"
)

@celery_app.task
def process_interaction(user_id: str, chat_id: str, response: str, strategy: str):
    logger.info(f"Processing interaction for user {user_id}, chat {chat_id} with strategy {strategy}")
    # Placeholder for processing logic (e.g., analytics, updating RL model)
    pass