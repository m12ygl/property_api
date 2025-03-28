
import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError

# Install Chromium
subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the Property Scout API. Use /search-properties."}

@app.get("/search-properties")
def search_properties(location: str = "London", max_price: Optional[int] = None):
    listings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        search_url = f"https://www.rightmove.co.uk/property-for-sale/find.html?searchLocation={location}&radius=5&minBedrooms=1&sortType=6&index=0"
        if max_price:
            search_url += f"&maxPrice={max_price}"

        try:
            page.goto(search_url, timeout=60000)

            # Accept cookies
            try:
                page.wait_for_selector("button#onetrust-accept-btn-handler", timeout=5000)
                page.click("button#onetrust-accept-btn-handler")
            except TimeoutError:
                pass

            # Try to wait for listings
            page.wait_for_selector(".propertyCard-wrapper", timeout=30000)

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

        except TimeoutError as te:
            screenshot_path = "/tmp/debug.png"
            page.screenshot(path=screenshot_path, full_page=True)
            return {
                "error": f"Timeout waiting for properties: {str(te)}",
                "screenshot_url": "/debug-screenshot"
            }
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
        finally:
            browser.close()

    return listings

@app.get("/debug-screenshot")
def get_screenshot():
    return FileResponse("/tmp/debug.png", media_type="image/png")
