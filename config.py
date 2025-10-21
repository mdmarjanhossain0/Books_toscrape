import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_KEY = os.getenv("API_KEY", "supersecretkey123")
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "books_db")

settings = Settings()
