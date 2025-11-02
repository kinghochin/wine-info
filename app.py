import os
import json
import re
import asyncio
from typing import List
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, field_validator
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


class WaitroseWineDetail(BaseModel):
    product_name: str = Field(..., description="Name of the wine product.")
    price: str | None = Field(None, description="Current price of the wine.")
    volume: str | None = Field(None, description="Bottle size (e.g., 75cl).")
    image_url: str | None = Field(None, description="Primary product image URL.")
    product_description: str | None = Field(None, description="Wine description text.")
    country: str | None = Field(None, description="Country of origin.")
    region: str | None = Field(None, description="Wine region.")
    grape_variety: str | None = Field(None, description="Grape variety or blend.")
    alcohol_content: str | None = Field(None, description="Alcohol percentage (ABV).")
    rating: str | None = Field(None, description="Average customer rating.")
    review_count: str | None = Field(None, description="Number of customer reviews.")
    original_price: str | None = Field(None, description="Original price if on sale.")
    stock_status: str | None = Field(None, description="Availability status.")
    tasting_notes: str | None = Field(
        None, description="Tasting notes and flavor profile."
    )
    food_pairing: str | None = Field(None, description="Recommended food pairings.")

    @field_validator("country")
    @classmethod
    def clean_country(cls, v):
        if v:
            # Remove "Country of Origin:" prefix
            return v.replace("Country of Origin:", "").strip()
        return v

    @field_validator("rating")
    @classmethod
    def clean_rating(cls, v):
        if v:
            # Extract just the number from "4.5 out of 5 stars" or "4out of 5 stars"
            match = re.search(r"(\d+\.?\d*)", v)
            return match.group(1) if match else v
        return v

    @field_validator("review_count")
    @classmethod
    def clean_review_count(cls, v):
        if v:
            # Extract just the number from "37 reviews"
            match = re.search(r"(\d+)", v)
            return match.group(1) if match else v
        return v


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

schema_details = {
    "name": "Wine Product Detail",
    "baseSelector": "main",
    "fields": [
        {
            "name": "product_name",
            "selector": "span.ProductHeader_name__ABMK2[data-testid='product-name']",
            "type": "text",
        },
        {
            "name": "price",
            "selector": "span[data-test='product-pod-price'] span",
            "type": "text",
        },
        {
            "name": "volume",
            "selector": "span.ProductSize_size__3kv3Y.ProductHeader_sizeMessage__e9XyK",
            "type": "text",
        },
        {
            "name": "image_url",
            "selector": "img[itemprop='image']",
            "type": "attribute",
            "attribute": "src",
        },
        {
            "name": "product_description",
            "selector": "section[id*='summary']",
            "type": "text",
        },
        {
            "name": "country",
            "selector": "li.GeneralDetails_origin__a45Oz",
            "type": "text",
        },
        {
            "name": "alcohol_content",
            "selector": "p.GeneralDetails_label__4obdI:contains('Alcohol') span.GeneralDetails_value__j1woc",
            "type": "text",
        },
        {
            "name": "rating",
            "selector": "span.Stars_srOnly__XeAlv",
            "type": "text",
        },
        {
            "name": "review_count",
            "selector": "span.StarRating_ratingText__jI4XA",
            "type": "text",
        },
        {
            "name": "original_price",
            "selector": "span[class*='wasPrice'], span[class*='WasPrice']",
            "type": "text",
        },
        {
            "name": "region",
            "selector": "p.GeneralDetails_label__4obdI:contains('Region') span.GeneralDetails_value__j1woc",
            "type": "text",
        },
        {
            "name": "grape_variety",
            "selector": "p.GeneralDetails_label__4obdI:contains('Grape') span.GeneralDetails_value__j1woc",
            "type": "text",
        },
        {
            "name": "stock_status",
            "selector": "span[class*='stock'], div[class*='availability']",
            "type": "text",
        },
        {
            "name": "tasting_notes",
            "selector": "div.swat-hosted-summary-text[role='region'], section[id*='tasting'] p, div[class*='tasting'] p",
            "type": "text",
        },
        {
            "name": "food_pairing",
            "selector": "section[id*='pairing'] p, div[class*='pairing'] p",
            "type": "text",
        },
    ],
}


# ---------------------------
# Scraper functions
# ---------------------------
async def scrape_waitrose(
    search_term: str, max_pages: int = 5
) -> List[WaitroseProduct]:
    """Scrape Waitrose product listing pages"""
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


async def scrape_waitrose_details(link: str) -> List[WaitroseWineDetail]:
    """Scrape individual Waitrose product detail page"""
    url = f"https://www.waitrose.com{link}"

    load_dotenv()

    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=False,
        # page_timeout=60000,  # 60 seconds timeout
        # delay_before_return=5.0,  # Increased wait time for dynamic content
    )
    css_strategy = JsonCssExtractionStrategy(schema_details)

    product_details: List[WaitroseWineDetail] = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # JavaScript to expand all accordion sections to reveal hidden content
        expand_accordions_js = """
        () => {
            const buttons = document.querySelectorAll('button[aria-expanded="false"]');
            buttons.forEach(btn => btn.click());
            return true;
        }
        """

        crawler_config = CrawlerRunConfig(
            js_only=False,
            js_code=expand_accordions_js,
            extraction_strategy=css_strategy,
            cache_mode=CacheMode.BYPASS,
            wait_for="h1",
            delay_before_return_html=3.0,
        )

        result = await crawler.arun(url=url, config=crawler_config)
        if result.success:
            try:
                data = json.loads(result.extracted_content)
                if data:
                    if isinstance(data, list):
                        product_details.extend([WaitroseWineDetail(**p) for p in data])
                    else:
                        product_details.append(WaitroseWineDetail(**data))
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw content: {result.extracted_content}")
            except Exception as e:
                print(f"Error creating WaitroseWineDetail: {e}")
                print(f"Data: {data}")
        else:
            print(
                f"Crawl failed: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}"
            )

    return product_details


# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="Waitrose Scraper API")


@app.get("/scrape", response_model=List[WaitroseProduct])
async def scrape(searchTerm: str = Query(..., description="Search term (e.g. 'wine')")):
    """Scrape Waitrose product listing pages"""
    products = await scrape_waitrose(searchTerm)
    return products


@app.get("/scrape-details", response_model=List[WaitroseWineDetail])
async def scrape_details(
    link: str = Query(..., description="Product link (e.g. '/ecom/products/...')")
):
    """Scrape individual Waitrose product detail page"""
    product_details = await scrape_waitrose_details(link)
    return product_details


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {}


# For local testing
if __name__ == "__main__":
    import uvicorn

    # Example usage
    async def test():
        # Test listing scraper
        print("Testing listing scraper...")
        products = await scrape_waitrose("wine", max_pages=1)
        print(f"Found {len(products)} products")
        if products:
            print(f"First product: {products[0].product_name}")

        # Test detail scraper
        print("\nTesting detail scraper...")
        details = await scrape_waitrose_details(
            "/ecom/products/gerard-bertrand-naturae-organic-merlot/692580-771933-771934"
        )
        if details:
            print(f"Product: {details[0].product_name}")
            print(f"Price: {details[0].price}")
            print(f"Country: {details[0].country}")
            print(f"ABV: {details[0].alcohol_content}")
            print(f"Rating: {details[0].rating}")

    # Uncomment to run test
    # asyncio.run(test())

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000)
