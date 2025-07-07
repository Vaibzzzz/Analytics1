import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # loads .env into environment

def get_engine():
    """
    Creates and returns a SQLAlchemy Engine using credentials from .env.
    """
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url, future=True, pool_pre_ping=True)