
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "skitrack"),
        user=os.getenv("POSTGRES_USER", "skitrack"),
        password=os.environ["POSTGRES_PASSWORD"],
    )
