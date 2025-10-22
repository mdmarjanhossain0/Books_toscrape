# book/routers.py
from fastapi import APIRouter, Depends
from database import get_database

from book.models import (
    BookSchema,
    ChangeLog
)

router = APIRouter()

@router.get("/books")
async def get_books(db=Depends(get_database)):
    books_cursor = db["book"].find()
    books = await books_cursor.to_list(length=100)

    # Convert ObjectIds to strings
    for book in books:
        book["_id"] = str(book["_id"])
    return books

@router.post("/books")
async def create_book(book: dict, db=Depends(get_database)):
    """
    Insert a single book.
    Example POST JSON body:
    {
        "title": "My Book",
        "author": "Author Name",
        "year": 2025
    }
    """
    result = await db["book"].insert_one(book)
    return {"inserted_id": str(result.inserted_id)}