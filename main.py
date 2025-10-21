from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List
from models import BookSchema
from database import books_collection, changes_collection
from services.auth import verify_api_key
from services.rate_limiter import rate_limit
from config import settings
from bson import ObjectId

app = FastAPI(title="Books Crawler API", version="1.0")

# ---------- Helper ----------
def book_serializer(book) -> dict:
    book["_id"] = str(book["_id"])
    return book

# ---------- Middleware ----------
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    api_key = request.headers.get("x-api-key")
    if api_key:
        await rate_limit(api_key)
    response = await call_next(request)
    return response

# ---------- Routes ----------
@app.get("/books", dependencies=[Depends(verify_api_key)])
async def get_books(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rating: Optional[str] = None,
    # sort_by: Optional[str] = Query(None, regex="^(rating|price|reviews)$"),
    sort_by: Optional[str] = Query(None),
    page: int = 1,
    limit: int = 10,
):
    query = {}
    if category:
        query["category"] = category
    if rating:
        query["rating"] = rating
    if min_price or max_price:
        query["price_incl_tax"] = {}
        if min_price:
            query["price_incl_tax"]["$gte"] = min_price
        if max_price:
            query["price_incl_tax"]["$lte"] = max_price

    skip = (page - 1) * limit
    cursor = books_collection.find(query).skip(skip).limit(limit)
    books = [book_serializer(b) async for b in cursor]
    return books

@app.get("/books/{book_id}", dependencies=[Depends(verify_api_key)])
async def get_book(book_id: str):
    book = await books_collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_serializer(book)

@app.get("/changes", dependencies=[Depends(verify_api_key)])
async def get_changes(limit: int = 20):
    cursor = changes_collection.find().sort("change_time", -1).limit(limit)
    return [book_serializer(c) async for c in cursor]
