from utils.utils import logger, config_path, get_db_connection
from celery import Celery
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
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interactions (user_id, chat_id, response, strategy)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, chat_id, response, strategy)
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Interaction saved to database.")
    except Exception as e:
        logger.error(f"Error saving interaction: {str(e)}")