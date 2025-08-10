import os
import logging
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize logging
logging.basicConfig(
    filename=config["logging"]["file"],
    level=getattr(logging, config["logging"]["level"]),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return psycopg2.connect(
            host=config["postgres"]["host"],
            port=config["postgres"]["port"],
            dbname=config["postgres"]["dbname"],
            user=config["postgres"]["user"],
            password=os.getenv("POSTGRES_PASSWORD"),
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
        raise

def validate_env_vars():
    required_vars = ["POSTGRES_PASSWORD", "GROQ_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")