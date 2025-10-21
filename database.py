import motor.motor_asyncio
import os

from decouple import config

MONGO_URI = config("MONGO_URI")
MONGO_DB = config("MONGO_DB", "book")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

books_collection = db["books"]
changes_collection = db["changes"]
