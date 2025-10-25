# main.py
from fastapi import FastAPI
from database import mongo_instance
from book.routers import router as book_router
from apscheduler.schedulers.background import BackgroundScheduler

from crawler import run_job

app = FastAPI(title="FastAPI Mongo Example")
scheduler = BackgroundScheduler()

def job():
    print("Running scheduled job!")
    run_job()

@app.on_event("startup")
async def startup_event():
    await mongo_instance.connect()
    scheduler.add_job(job, "interval", seconds=3600*1)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    await mongo_instance.close()
    scheduler.shutdown()

app.include_router(book_router, prefix="/api", tags=["Books"])
