from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

def book_collection_schema():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["title", "category", "price_incl_tax", "price_excl_tax",
                         "availability", "num_reviews", "rating", "image_url",
                         "source_url", "content_hash", "created_at"],
            "properties": {
                "title": {"bsonType": "string", "description": "Book title required"},
                "description": {"bsonType": "string", "description": "Optional description"},
                "category": {"bsonType": "string", "description": "Book category required"},
                "price_incl_tax": {"bsonType": "double", "minimum": 0, "description": "Price including tax"},
                "price_excl_tax": {"bsonType": "double", "minimum": 0, "description": "Price excluding tax"},
                "availability": {"bsonType": "string", "description": "Availability info"},
                "num_reviews": {"bsonType": "int", "minimum": 0, "description": "Number of reviews"},
                "rating": {"bsonType": "string", "description": "Book rating"},
                "image_url": {"bsonType": "string", "description": "Image URL"},
                "source_url": {"bsonType": "string", "description": "Source URL"},
                "crawl_timestamp": {"bsonType": "date", "description": "Crawl timestamp"},
                "crawl_status": {"bsonType": "string", "description": "Crawl status"},
                "raw_html_path": {"bsonType": "string", "description": "Path to raw HTML file"},
                "content_hash": {"bsonType": "string", "description": "Unique content hash"},
                "created_at": {"bsonType": "date"}
            }
        }
    }
    return validator




def change_log_schema():
    book_schema = book_collection_schema()["$jsonSchema"]["properties"]
    book_schema["_id"] = {
        "bsonType": "object"
    }
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["book_id", "details", "change_time"],
            "properties": {
                "book_id": {
                    "bsonType": "string",
                    "description": "The ID of the book being changed"
                },
                "details": {
                    "bsonType": "object",
                    "properties": book_schema
                },
                "change_time": {
                    "bsonType": "date",
                    "description": "The time the change was made"
                }
            }
        }
    }

    return validator

def url_record_schema():
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["url", "type", "status", "crawl_time"],
            "properties": {
                "url": {
                    "bsonType": "string"
                },
                "type": {
                    "bsonType": "string"
                },
                "status": {
                    "bsonType": "bool"
                },
                "timestamp": {
                    "bsonType": "date"
                }
            }
        }
    }