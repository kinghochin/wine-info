import os
import json
import asyncio
from typing import List
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
    CacheMode,
)


# ---------------------------
# Pydantic schema for product
# ---------------------------
class WaitroseProduct(BaseModel):
    product_name: str = Field(..., description="Name of the product in listing.")
    product_url: str = Field(..., description="URL link to product detail.")
    price: str | None = Field(None, description="Price displayed in listing.")
    country: str | None = Field(None, description="Country.")
    rating: str | None = Field(None, description="Rating displayed in listing.")
    image_url: str | None = Field(None, description="Primary image from listing.")


# ---------------------------
# CSS extraction schema
# ---------------------------
schema = {
    "name": "Product Block",
    "baseSelector": "article[data-testid='product-pod']",
    "fields": [
        {
            "name": "product_name",
            "selector": "h2[data-testid='product-pod-name']",
            "type": "text",
        },
        {
            "name": "product_url",
            "selector": "a.nameLink___iKLUD",
            "type": "attribute",
            "attribute": "href",
        },
        {"name": "price", "selector": "span.redText___eRw74", "type": "text"},
        {
            "name": "country",
            "selector": "div[data-testid] > span[data-testid='typography']",
            "type": "text",
        },
        {"name": "rating", "selector": "span.srOnly___sJU_Z", "type": "text"},
        {
            "name": "image_url",
            "selector": "img",
            "type": "attribute",
            "attribute": "src",
        },
    ],
}


# ---------------------------
# Scraper function
# ---------------------------
async def scrape_waitrose(
    search_term: str, max_pages: int = 5
) -> List[WaitroseProduct]:
    url = f"https://www.waitrose.com/ecom/shop/search?&searchTerm={search_term}"
    load_dotenv()

    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
    )
    css_strategy = JsonCssExtractionStrategy(schema)

    products: List[WaitroseProduct] = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(max_pages):
            load_more_js = """
                () => {
                    const btn = document.querySelector('button[data-testid="button-load-more"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                }
            """

            wait_for_code = f"""
                () => {{
                    return document.querySelectorAll('article[data-testid="product-pod"]').length > {len(products)};
                }}
            """

            crawler_config = CrawlerRunConfig(
                js_only=True if page > 0 else False,
                js_code=load_more_js if page > 0 else None,
                extraction_strategy=css_strategy,
                css_selector="article[data-testid='product-pod']",
                session_id="waitrose_session",
                wait_for=wait_for_code if page > 0 else None,
                cache_mode=CacheMode.BYPASS,
            )

            result = await crawler.arun(url=url, config=crawler_config)
            if result.success:
                batch = json.loads(result.extracted_content)
                if not batch:
                    break
                products.extend([WaitroseProduct(**p) for p in batch])

                if "button-load-more" not in result.html:
                    break
            else:
                break

    return products


# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="Waitrose Scraper API")


@app.get("/scrape", response_model=List[WaitroseProduct])
async def scrape(searchTerm: str = Query(..., description="Search term (e.g. 'wine')")):
    products = await scrape_waitrose(searchTerm)
    return products


# Optional: avoid favicon.ico 404
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {}
