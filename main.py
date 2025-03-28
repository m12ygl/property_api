
import subprocess
from fastapi import FastAPI, Query
from typing import Optional
from playwright.sync_api import sync_playwright

# One-time Chromium install
subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/search-properties")
def search_properties(location: str = "London", max_price: Optional[int] = None):
    listings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        search_url = f"https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation={location}&radius=5&minBedrooms=1&sortType=6&index=0"
        if max_price:
            search_url += f"&maxPrice={max_price}"

        page.goto(search_url, timeout=60000)
        page.wait_for_selector(".propertyCard-wrapper", timeout=10000)

        cards = page.query_selector_all(".propertyCard-wrapper")

        for card in cards[:10]:
            title = card.query_selector("h2.propertyCard-title")
            title_text = title.inner_text().strip() if title else "No title"

            price = card.query_selector(".propertyCard-priceValue")
            price_text = price.inner_text().strip() if price else "No price"

            link = card.query_selector("a.propertyCard-link")
            link_href = "https://www.rightmove.co.uk" + link.get_attribute("href") if link else "#"

            image = card.query_selector("img.propertyCard-img")
            image_src = image.get_attribute("src") if image else ""

            summary = f"• {title_text}\n• Price: {price_text}\n• Link: {link_href}"

            listings.append({
                "title": title_text,
                "price": price_text,
                "url": link_href,
                "image": image_src,
                "summary": summary
            })

        browser.close()

    return listings
