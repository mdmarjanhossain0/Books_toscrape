# main.py
from fastapi import FastAPI
from database import mongo_instance
from book.routers import router as book_router

app = FastAPI(title="FastAPI Mongo Example")

@app.on_event("startup")
async def startup_event():
    await mongo_instance.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await mongo_instance.close()

app.include_router(book_router, prefix="/api", tags=["Books"])
