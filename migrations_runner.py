import os
import importlib.util
import asyncio

MIGRATIONS_DIR = "migrations"
MIGRATIONS_TRACKER = "migrations_collection"

from database import MongoDB

async def run_migration(file_path):
    spec = importlib.util.spec_from_file_location("migration", file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    await mod.upgrade()

async def main():
    db_conn = MongoDB()
    applied = await db_conn.db[MIGRATIONS_TRACKER].find({}, {"name":1})
    applied_files = [doc["name"] async for doc in applied]

    for filename in sorted(os.listdir(MIGRATIONS_DIR)):
        if filename.endswith(".py") and filename not in applied_files and filename != "__init__.py":
            print(f"Applying migration: {filename}")
            await run_migration(os.path.join(MIGRATIONS_DIR, filename))
            await db_conn.db[MIGRATIONS_TRACKER].insert_one({"name": filename})
    await db_conn.close()

if __name__ == "__main__":
    asyncio.run(main())
