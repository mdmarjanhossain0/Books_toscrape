import asyncio
import platform


# if platform.system() == "Windows":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import math

from ebay.MainOpsV2 import EbayScraper
from ebay.models import SearchQuery, EbayData, Proxy
import requests
from bs4 import BeautifulSoup
import os
import math



from playwright.async_api import async_playwright
from datetime import datetime


HEADLESS = False


BASE_DIR = "./test_outputs"
# logging.basicConfig(
# 	filename=f"{BASE_DIR}/proxy_test.log",
# 	filemode="a",
# 	level=logging.INFO,
# 	format="%(asctime)s - %(levelname)s - %(message)s",
# 	datefmt="%Y-%m-%d %H:%M:%S",
# )
if not os.path.exists(BASE_DIR):
	os.makedirs(BASE_DIR)





class EbayScraperEngine:
	BLOCK_TITLE = "Pardon our interruption..."
	
	def __init__(self, search_queries, proxies):
		self.search_queries = search_queries
		self.proxies = proxies
		self.current_proxy = None
		if len(proxies):
			self.current_proxy = proxies.pop()
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate',
			'Connection': 'keep-alive',
		}
		self.list_urls = []
		self.list_blocked = []
		self.list_completed = []
		self.BATCH_SIZE = 3
		self.MODE = "LIST"
		self.IS_LIST_MY_IP_BLOCK = False
		self.IS_DETAIL_MY_IP_BLOCK = False

		self.playwright = None
		self.browser = None
		self.context = None
		self.page_queue = asyncio.Queue()
		self.pages = []
		self.pool_size = self.BATCH_SIZE
	





	async def start(self):
		print("playwright start")
		self.playwright = await async_playwright().start()
		self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
		self.context = await self.browser.new_context()

		for _ in range(self.BATCH_SIZE):
			page = await self.context.new_page()
			self.pages.append(page)
			await self.page_queue.put(page)
		print(f"[POOL] Initialized {self.BATCH_SIZE} pages.")

	async def acquire_page(self):
		"""Get an available page from the pool."""
		page = await self.page_queue.get()
		print("[POOL] Page acquired.")
		return page

	async def release_page(self, page):
		"""Return a page to the pool."""
		await self.page_queue.put(page)
		print("[POOL] Page released.")

	async def close(self):
		"""Close browser and stop Playwright."""
		await self.browser.close()
		await self.playwright.stop()
		print("[POOL] Closed Playwright.")

	# async def __aenter__(self):
	# 	await self.start()
	# 	return self

	async def __aexit__(self, exc_type, exc, tb):
		await self.close()
		
	def convert_ebay_url(self, url):
		# return url
		if "ebay.co.uk" in url:
			return url.replace("ebay.co.uk", "ebay.com")
		return url

	async def browser_request(self, obj):
		page = await self.acquire_page()
		url = obj["url"].split("?")[0]
		url = self.convert_ebay_url(url)
		try:
			await page.goto(url, wait_until="load", timeout=15*1000)
			await page.wait_for_selector(".vi-body", timeout=10*1000)
			return await page.content()
		except Exception as e:
			print(f"Playwright exception in get_detail: {e}")
			return None

	async def python_request(self, obj, proxy=None):
		try:
			response = requests.get(obj["url"], headers=self.headers)
			# print(response.text)
			return response.text
		except Exception as e:
			print(f"Python exception in scrape_by_python: {e}")
			return None
	
	def update_proxy(self):
		try:
			self.current_proxy = self.proxies.pop()
		except:
			self.current_proxy = None
	
	async def fetch_data(self, obj):
		if self.current_proxy is None:
			self.update_proxy()

		if self.current_proxy:
			response = await self.python_request(obj)
			soup = BeautifulSoup(response, parser="html.parser")
			if EbayScraperEngine.is_block_verify(soup):
				self.update_proxy()
				return await self.browser_request(obj)
			else:
				return response
		else:
			return await self.browser_request(obj)
	
	async def get_detail(self, url, page):
		print(url)
		try:
			await page.goto(url, wait_until="load", timeout=20*1000)
			await page.wait_for_selector(".vi-body", timeout=10*1000)
			return await page.content()
		except Exception as e:
			print(f"Playwright exception in get_detail: {e}")
			return None


	async def fetch_browser_batch(self, batch):
		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=HEADLESS)
			context = await browser.new_context()
			# Intercept image requests
			await context.route(
				"**/*",
				lambda route: asyncio.create_task(
					route.abort()
					if route.request.resource_type == "image"
					else route.continue_()
				)
			)
			pages = [await context.new_page() for _ in range(len(batch))]

			tasks = []
			for url_obj, page in zip(batch, pages):
				print(url_obj["url"])
				tasks.append(self.get_detail(url_obj["url"], page))
			data = await asyncio.gather(*tasks, return_exceptions=True)
			return data
		return []



	def list_page_to_cards(self, soup):
		try:
			ul = soup.find(class_="srp-results srp-list clearfix")
			# card_list = ul.find_all(class_='s-item') if ul else []
			card_list = ul.find_all(class_='s-card s-card--horizontal s-card--dark-solt-links-blue') if ul else []
			return card_list
		except:
			return []
	
	@staticmethod
	def is_block_verify(soup):
		title = soup.title.string
		if title == EbayScraperEngine.BLOCK_TITLE:
			return True
		else:
			return False

	
	@staticmethod
	def card_list_to_dict(card_list):
		data_list = []
		for card in card_list:
			try:
				link = card.find('a', class_='s-item__link').get('href')
				card_id = card["id"]
				try:
					sold_date = card.find_all("span", class_="POSITIVE")[0]
					sold_date = " ".join(sold_date.text.split()[1:])
					sold_date = datetime.strptime(sold_date, "%d %b %Y")
				except:
					sold_date = None
					return None
				
				try:
					heading = card.find(
						'span', {'role': 'heading'}).get_text(strip=True)
				except:
					heading = None

				try:
					status = card.find('span', class_='SECONDARY_INFO').get_text(
						strip=True)
				except:
					status = None

				postage = None
				postage_currency = None
				try:
					postage_label = card.find(class_="s-item__shipping s-item__logisticsCost")
					if postage_label != None:
						postage_label = postage_label.text.split(" ")[1]
						postage = postage_label[1:]
						postage_currency = postage_label[:1]
				except BaseException as e:
					print("postage exception")
					postage = None
					postage_currency = None

				try:
					price_label = card.find(
						'span', class_='s-item__price').get_text(strip=True)
					# print(f"price label {price_label}")
					if price_label != None:
						price = price_label[1:]
						price_currency = price_label[:1]
				except BaseException as e:
					print("price exception")
					# print(e)
					price = None
					price_currency = None
				# print("After price")
				try:
					sellerInfo = card.find(
						'span', class_='s-item__seller-info-text').get_text(strip=True)
				except:
					sellerInfo = None

				try:
					itemLocation = card.find(
						'span', class_='s-item__location s-item__itemLocation').get_text(strip=True)
					
					if itemLocation:
						itemLocation = "".join(itemLocation.split()[1:])
				except:
					itemLocation = None

				try:
					thumbnail = card.find("div", class_="s-item__image-wrapper image-treatment").find("img")["src"]
				except:
					thumbnail = None

				card_data = {
						'heading': heading,
						'status': status,
						'price': price,
						'price_currency': price_currency,
						# 'postage': safe_decimal(postage),
						'postage_currency': postage_currency,
						# 'postage_location': postage_location,
						'seller_info': sellerInfo,
						'item_location': itemLocation,
						'link': link,
						'card_id': card_id,
						'sold_date': sold_date,
						'thumbnail': thumbnail
					}
				data_list.append(card_data)
			except BaseException as e:
				print(e, "Card info error")
				data_list.append(None)
		return data_list

	async def test(self):
		# async with async_playwright() as p:
		# 	browser = await p.chromium.launch(headless=HEADLESS)
		# 	page = await browser.new_page()
		# 	await page.goto("https://www.ebay.com")
		# 	print(await page.title())
		# 	await browser.close()
		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=HEADLESS)
			context = await browser.new_context()

			pages = [await context.new_page() for _ in range(50)]
			await asyncio.sleep(5)

	def start_list_scraping(self):
		batch_size = self.BATCH_SIZE
		async def run_batches():
			for i in range(0, len(self.list_urls), batch_size):
				batch = self.list_urls[i:i+batch_size]
				data = await asyncio.gather(*(self.fetch_data(url_obj) for url_obj in batch))
				for i, page_data in enumerate(data):
					soup = BeautifulSoup(page_data, parser="html.parser")
					url_obj = self.list_urls[i]
					if EbayScraperEngine.is_block_verify(soup):
						self.list_blocked.append(
							url_obj
						)
					else:
						cards = self.list_page_to_cards(soup)
						card_info_list = EbayScraperEngine.card_list_to_dict(cards)
						db_objs = []
						print(card_info_list)
						for card_info in card_info_list:
							if card_info is None:
								continue
							# EbayData(
							# 	search_query_id=url_obj["query_id"],
							# 	card_id=card_info["card_id"],
							# 	ebay_id=None,
							# 	heading=card_info["heading"],
							# 	brand=card_info["brand"],
							# 	status=card_info["status"],
							# 	price=card_info["price"],
							# 	price_currency=card_info["price_currency"]
							# )
							db_objs.append(
								EbayData(**card_info)
							)
						EbayData.objects.bulk_create(db_objs)
						self.list_completed.append(
							url_obj
						)
		
		# asyncio.run(self.start())
		asyncio.run(run_batches())

	async def start_batch_scraping(self):
		batch_size = self.BATCH_SIZE
		for i in range(0, len(self.list_urls), batch_size):
			batch = self.list_urls[i:i+batch_size]
			data = await self.fetch_browser_batch(batch)
			# continue
			for i, page_data in enumerate(data):
				soup = BeautifulSoup(page_data, parser="html.parser")
				url_obj = self.list_urls[i]
				print(EbayScraperEngine.is_block_verify(soup))
				continue
				if EbayScraperEngine.is_block_verify(soup):
					self.list_blocked.append(
						url_obj
					)
				else:
					cards = self.list_page_to_cards(soup)
					card_info_list = EbayScraperEngine.card_list_to_dict(cards)
					db_objs = []
					print(card_info_list)
					for card_info in card_info_list:
						if card_info is None:
							continue
						db_objs.append(
							EbayData(**card_info)
						)
					EbayData.objects.bulk_create(db_objs)
					self.list_completed.append(
						url_obj
					)




	def scrape_list(self):
		for query_obj in self.search_queries:
			total_pages = int(math.ceil(query_obj.number_of_items / 60))
			for page in range(1, total_pages + 1):
				url = f"https://www.ebay.com/sch/i.html?_from=R40&_nkw={query_obj.query}&_sacat=0&LH_Sold={1}&rt=nc&LH_PrefLoc=1&_pgn={page}"
				info = {
					"url": url,
					"query_id": query_obj.pk
				}
				self.list_urls.append(info)
		print(len(self.list_urls))
		# print(self.list_urls)
		asyncio.run(self.start_batch_scraping())


				

				

			
