import os
import psycopg2

def get_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)

    return psycopg2.connect(
        host="localhost",
        database="catalogo_filmes",
        user="postgres",
        password="1234"
    )