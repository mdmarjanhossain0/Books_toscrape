import os
import json
from datetime import datetime
from models import (
    BookSchema
)

MIGRATIONS_DIR = "migrations"
DB_NAME = "bookscraper"
COLLECTION_NAME = "books"

def get_current_fields():
    return set(BookSchema.__fields__.keys())

def load_last_fields():
    last_file = os.path.join(MIGRATIONS_DIR, "last_model.json")
    if os.path.exists(last_file):
        with open(last_file, "r") as f:
            return set(json.load(f))
    return set()

def save_current_fields(fields):
    with open(os.path.join(MIGRATIONS_DIR, "last_model.json"), "w") as f:
        json.dump(list(fields), f)

def generate_migration(new_fields):
    if not new_fields:
        print("No new fields detected.")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_add_fields.py"
    path = os.path.join(MIGRATIONS_DIR, filename)

    with open(path, "w") as f:
        f.write("import asyncio\n")
        f.write("from motor.motor_asyncio import AsyncIOMotorClient\n")
        f.write("import os\n\n")
        f.write(f"MONGO_URI = os.getenv('MONGO_URI', 'your_atlas_connection_string_here')\n")
        f.write(f"DB_NAME = '{DB_NAME}'\n")
        f.write(f"COLLECTION_NAME = '{COLLECTION_NAME}'\n\n")
        f.write("async def upgrade():\n")
        f.write("    client = AsyncIOMotorClient(MONGO_URI)\n")
        f.write("    db = client[DB_NAME]\n")
        f.write("    collection = db[COLLECTION_NAME]\n")
        for field in new_fields:
            f.write(f"    await collection.update_many({{{field}: {{'$exists': False}}}}, {{'$set': {{'{field}': ''}}}})\n")
        f.write("    client.close()\n\n")
        f.write("async def downgrade():\n")
        f.write("    client = AsyncIOMotorClient(MONGO_URI)\n")
        f.write("    db = client[DB_NAME]\n")
        f.write("    collection = db[COLLECTION_NAME]\n")
        for field in new_fields:
            f.write(f"    await collection.update_many({{}}, {{'$unset': {{'{field}': ''}}}})\n")
        f.write("    client.close()\n\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    asyncio.run(upgrade())\n")

    print(f"Migration generated: {path}")

def main():
    os.makedirs(MIGRATIONS_DIR, exist_ok=True)
    current_fields = get_current_fields()
    last_fields = load_last_fields()
    new_fields = current_fields - last_fields
    generate_migration(new_fields)
    save_current_fields(current_fields)

if __name__ == "__main__":
    main()
