from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_engine() -> Engine:
    try:
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        # PostgreSQL connection URI format
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        engine = create_engine(database_url)
        
        # ✅ FIX: Use text() to wrap raw SQL query
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return engine
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")

def get_connection():
    engine = get_db_engine()
    return engine.connect()
