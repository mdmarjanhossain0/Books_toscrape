from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BookSchema(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    price_incl_tax: float
    price_excl_tax: float
    availability: str
    num_reviews: int
    rating: str
    image_url: str
    source_url: str
    raw_html_path: Optional[str] = None
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    crawl_status: str = "success"
    content_hash: str
    created_at: datetime

class ChangeLog(BaseModel):
    book_id: str
    details: BookSchema
    change_time: datetime = Field(default_factory=datetime.utcnow)


class UrlRecordSchema(BaseModel):
    url: str
    type: str
    status: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
