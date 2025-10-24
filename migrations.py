from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

from database import mongo_instance
from book.schemas import (
    book_collection_schema,
    change_log_schema,
    url_record_schema
)

async def create_schema(db, name, validator):
    await db.create_collection(
            name,
            validator=validator,
            validationLevel="strict"
        )

async def update_schema(db, name, validator):
    await db.command({
            "collMod": name,
            "validator": validator,
            "validationLevel": "strict"
        })


async def create_books_collection(db, name, validator):
    if name not in await db.list_collection_names():
        await create_schema(db, name, validator)
        print("✅ Collection 'book' created with schema validation")
    else:
        await update_schema(db, name, validator)
        print("✅ Collection 'book' validator updated")

    await db[name].create_index("content_hash", unique=True)
    await db[name].create_index("source_url", unique=True)
    print("✅ Unique indexes on 'content_hash' and 'source_url' applied")

async def create_change_log_collection(db, name, validator):
    if name not in await db.list_collection_names():
        await create_schema(db, name, validator)
        print("✅ Collection 'changelog' created with schema validation")
    else:
        await update_schema(db, name, validator)
        print("✅ Collection 'changelog' validator updated")

async def url_record_collection(db, name, validator):
    if name not in await db.list_collection_names():
        await create_schema(db, name, validator)
        print(f"✅ Collection {name} created with schema validation")
    else:
        await update_schema(db, name, validator)
        print(f"✅ Collection {name} validator updated")
    await db[name].create_index("url", unique=True)
    print("✅ Unique indexes on 'url_record_collection' and 'url' applied")


async def start_migrations():
    await mongo_instance.connect()
    db = mongo_instance.db
    await create_books_collection(db, "book", book_collection_schema())
    await create_change_log_collection(db, "changelog", change_log_schema())
    await url_record_collection(db, "url_record", url_record_schema())


if __name__ == "__main__":
    asyncio.run(start_migrations())
