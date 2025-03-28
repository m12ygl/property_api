import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import os

# Ensure Chromium is installed
subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Property API is running. Use /search-properties?town=Harrow"}

@app.get("/search-properties")
async def search_properties(
    town: str = Query(..., description="Town to search in"),
    max_price: int = Query(500000, description="Max property price"),
    radius: float = Query(0.25, ge=0.25, description="Search radius in miles (min 0.25)")
):
    search_url = (
        f"https://www.rightmove.co.uk/property-for-sale/find.html"
        f"?searchType=SALE"
        f"&locationIdentifier={town}"
        f"&radius={radius}"
        f"&maxPrice={max_price}"
        f"&sortType=6"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(search_url, timeout=60000)

            # Wait for property cards
            await page.wait_for_selector(".propertyCard-wrapper", timeout=40000)
            cards = await page.locator(".propertyCard-wrapper").all()
            results = []

            for card in cards[:5]:
                title = await card.locator("h2.propertyCard-title").text_content() or "No title"
                price = await card.locator(".propertyCard-priceValue").text_content() or "No price"
                link = await card.locator("a[data-test='property-header']").get_attribute("href")
                full_link = f"https://www.rightmove.co.uk{link}" if link else "N/A"

                results.append({
                    "title": title.strip(),
                    "price": price.strip(),
                    "link": full_link
                })

            await browser.close()
            return results

        except PlaywrightTimeout:
            screenshot_path = "/tmp/debug.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            await browser.close()
            return {
                "error": "Timeout waiting for properties.",
                "screenshot": "/debug-screenshot"
            }
        except Exception as e:
            await browser.close()
            return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/debug-screenshot")
def get_screenshot():
    path = "/tmp/debug.png"
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return JSONResponse(content={"error": "No screenshot found."}, status_code=404)