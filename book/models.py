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
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    crawl_status: str = "success"
    raw_html_path: Optional[str] = None
    content_hash: str

class ChangeLog(BaseModel):
    book_id: str
    field_changed: str
    old_value: str
    new_value: str
    change_time: datetime = Field(default_factory=datetime.utcnow)
