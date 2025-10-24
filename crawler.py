import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from slugify import slugify

from typing import List
from database import mongo_instance

from book.models import (
    BookSchema,
    ChangeLog,
    UrlRecordSchema
)


class CrawlerEngine:
    BASE_URL = "https://books.toscrape.com/"
    CATALOGUE_URL = BASE_URL + "catalogue/page-{}.html"
    CONCURRENT_REQUESTS = 10
    RETRIES = 3
    TIMEOUT = 15

    def __init__(self, output_dir: str = "./data/snapshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def fetch(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        for attempt in range(1, self.RETRIES + 1):
            try:
                response = await client.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.text
            except httpx.RequestError as e:
                print(f"[Attempt {attempt}] Network error: {e}")
            except httpx.HTTPStatusError as e:
                print(f"[Attempt {attempt}] HTTP error {e.response.status_code}: {url}")
            await asyncio.sleep(attempt)  # exponential backoff
        print(f"❌ Failed after {self.RETRIES} retries: {url}")
        return None

    async def get_total_pages(self, client: httpx.AsyncClient) -> int:
        first_page = await self.fetch(client, self.CATALOGUE_URL.format(1))
        if not first_page:
            return 1
        soup = BeautifulSoup(first_page, "html.parser")
        pager = soup.select_one("li.current")
        if pager:
            text = pager.text.strip()
            try:
                total_pages = int(text.split("of")[-1].strip())
                return total_pages
            except ValueError:
                pass
        return 1

    async def crawl_page(self, client: httpx.AsyncClient, url, db) -> list[str]:
        html = await self.fetch(client, url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        books = soup.select("article.product_pod h3 a")
        book_links = [
            self.BASE_URL + "catalogue/" + a["href"].replace("../../../", "")
            for a in books
        ]
        print(f"✅ Page {url}: Found {len(book_links)} books")
        await db["url_record"].update_one(
            {"url": url},
            [{"$set": {"status": True}}],
            upsert=False
        )
        await self.save_urls(db, book_links, type="detail")
        return book_links



    async def book_info_create_or_update(self, db, book):
        book = book.dict()
        old_book = await db["book"].find_one({"source_url": book["source_url"]})
        if old_book:
            changelog = ChangeLog(
                book_id=old_book["book_id"],
                details=book
            )
            book["created_at"] = old_book["created_at"]
            await db["changelog"].insert_one(changelog)
        print("insert book")
        await db["book"].update_one(
            {"source_url": book["source_url"]},
            [{"$set": book}],
            upsert=True
        )

        
    async def crawl_book(self, client: httpx.AsyncClient, url: str, db) -> Optional[BookSchema]:
        html = await self.fetch(client, url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        try:
            title = soup.select_one(".product_main h1").text.strip()
            price_incl = soup.select_one("th:contains('Price (incl. tax)') + td").text.strip().replace("£", "")
            price_excl = soup.select_one("th:contains('Price (excl. tax)') + td").text.strip().replace("£", "")
            availability = soup.select_one(".availability").text.strip()
            category = soup.select("ul.breadcrumb li a")[-1].text.strip()
            num_reviews = int(soup.select_one("th:contains('Number of reviews') + td").text.strip())
            rating = soup.select_one(".star-rating")["class"][1]
            image_url = soup.select_one("div.item.active img")["src"].replace("../../", self.BASE_URL)

            desc_el = soup.select_one("#product_description + p")
            description = desc_el.text.strip() if desc_el else ""

            content_hash = hashlib.md5(html.encode("utf-8")).hexdigest()

            html_path = self.output_dir / f"{slugify(title)}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            await db["url_record"].update_one(
                    {"url": url},
                    [{"$set": {"status": True}}],
                    upsert=False
                )
            book = BookSchema(
                title=title,
                description=description,
                category=category,
                price_incl_tax=float(price_incl),
                price_excl_tax=float(price_excl),
                availability=availability,
                num_reviews=num_reviews,
                rating=rating,
                image_url=image_url,
                source_url=url,
                raw_html_path=str(html_path),
                content_hash=content_hash,
                created_at=datetime.utcnow()
            )
            print("book schema")
            await self.book_info_create_or_update(db, book)
            return book
        except Exception as e:
            print(f"⚠️ Parsing error for {url}: {e}")
            return None

    async def save_urls(self, db, urls: List[str], type="list"):
        try:
            records = [
                UrlRecordSchema(url=url, type=type, status=False).dict()
                for url in urls
            ]
            result = await db["url_record"].insert_many(records, ordered=False)
        except:
            pass


    async def scrape_detai_urls(self, db, urls):
        async with httpx.AsyncClient(headers={"User-Agent": "BookCrawler/1.0"}) as client:
                sem = asyncio.Semaphore(self.CONCURRENT_REQUESTS)
                async def sem_task(url):
                    async with sem:
                        return await self.crawl_book(client, url["url"], db)

                detail_tasks = [sem_task(url) for url in urls]
                all_books = await asyncio.gather(*detail_tasks)

                books = [b.dict() for b in all_books if b]
                print(f"\n✅ Crawled {len(books)} books successfully.")
                # await db["book"].create_index("content_hash", unique=True)

                print(f"📦 Data saved to db")

    async def run(self):
        await mongo_instance.connect()
        db = mongo_instance.db
        urls = await db["url_record"].find({"status": False, "type": "list"}).to_list(length=None)
        print(urls)
        
        if len(urls) < 1 or True:
            async with httpx.AsyncClient(headers={"User-Agent": "BookCrawler/1.0"}) as client:
                print("not enter to create url")
                # total_pages = 3
                total_pages = await self.get_total_pages(client)
                print(f"📘 Total pages detected: {total_pages}")
                urls = [self.CATALOGUE_URL.format(page_number) for page_number in range(1, total_pages + 1)]
                await self.save_urls(db, urls)
        async with httpx.AsyncClient(headers={"User-Agent": "BookCrawler/1.0"}) as client:
            page_tasks = [self.crawl_page(client, url, db) for url in urls]
            await asyncio.gather(*page_tasks)
                

        all_book_urls = await db["url_record"].find({"status": False, "type": "detail"}).to_list(length=None)
        print(f"detail url {len(all_book_urls)}")
        await self.scrape_detai_urls(db, all_book_urls)
        
        # result = await db["url_record"].delete_many({})
        await mongo_instance.close()


if __name__ == "__main__":
    asyncio.run(CrawlerEngine().run())
