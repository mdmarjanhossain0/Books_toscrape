from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

from database import mongo_instance
from book.schemas import (
    book_collection_schema,
    change_log_schema
)


async def create_books_collection(db):
    # Create collection if it doesn't exist
    if "book" not in await db.list_collection_names():
        await db.create_collection(
            "book",
            validator=book_collection_schema(),
            validationLevel="strict"
        )
        print("✅ Collection 'book' created with schema validation")
    else:
        # Update validator if collection exists
        await db.command({
            "collMod": "book",
            "validator": book_collection_schema(),
            "validationLevel": "strict"
        })
        print("✅ Collection 'book' validator updated")

    # Ensure unique indexes
    await db["book"].create_index("content_hash", unique=True)
    await db["book"].create_index("source_url", unique=True)
    print("✅ Unique indexes on 'content_hash' and 'source_url' applied")


async def create_change_log_collection(db):
    if "changelog" not in await db.list_collection_names():
        await db.create_collection(
            "changelog",
            validator=change_log_schema(),
            validationLevel="strict"
        )
        print("✅ Collection 'changelog' created with schema validation")
    else:
        await db.command({
            "collMod": "changelog",
            "validator": change_log_schema(),
            "validationLevel": "strict"
        })
        print("✅ Collection 'changelog' validator updated")


async def start_migrations():
    await mongo_instance.connect()
    db = mongo_instance.db  # No await here
    await create_books_collection(db)
    await create_change_log_collection(db)


if __name__ == "__main__":
    asyncio.run(start_migrations())
