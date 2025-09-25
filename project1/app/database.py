import time
from databases import Database
from sqlalchemy import create_engine, MetaData
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/mydb")

database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)

def wait_for_db(retries=10, delay=3):
    """
    DB가 준비될 때까지 재시도
    """
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                dbname="mydb",
                user="myuser",
                password="mypassword",
                host="db",
                port="5432",
            )
            conn.close()
            print("Database is ready!")
            return
        except psycopg2.OperationalError:
            print(f"Database not ready, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Database not ready after several retries")

# FastAPI 시작 전에 호출
wait_for_db()