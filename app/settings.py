import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:dbpass@127.0.0.1:5555/db"
)
ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
]

DEFAULT_DISCOUNT = 0
