import time
from fastapi import HTTPException, status
from config import settings

rate_limit_cache = {}

async def rate_limit(api_key: str):
    limit = settings.RATE_LIMIT
    window = 3600  # 1 hour

    current_time = int(time.time())
    user_data = rate_limit_cache.get(api_key, {"count": 0, "start": current_time})

    if current_time - user_data["start"] > window:
        user_data = {"count": 0, "start": current_time}

    if user_data["count"] >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

    user_data["count"] += 1
    rate_limit_cache[api_key] = user_data
