# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends

from decouple import config

MONGO_URI = config("MONGO_URI")

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client["bookscraper"]
        print("✅ MongoDB connected to:", self.db.name)

    async def close(self):
        if self.client:
            self.client.close()
            print("❌ MongoDB connection closed.")

mongo_instance = MongoDB()

# ✅ Normal async generator dependency (not @contextmanager)
async def get_database():
    yield mongo_instance.db
