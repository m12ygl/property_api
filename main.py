import subprocess
import time
from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import uvicorn

subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

RIGHTMOVE_BASE_URL = "https://www.rightmove.co.uk/"

@app.get("/")
def read_root():
    return {"message": "UK Property Scout is live."}

@app.get("/search-properties")
async def search_properties(
    town: str = Query(..., description="Town to search in"),
    max_price: int = Query(500000, description="Maximum price filter"),
    radius: float = Query(0.25, description="Search radius in miles")
):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(RIGHTMOVE_BASE_URL)
            await page.fill("input#searchLocation", town)
            await page.click("button[data-test='submit-button']")

            await page.wait_for_url("**/property-for-sale/**", timeout=10000)

            # Adjust filters
            await page.click("button[data-test='priceDropdown-toggle']")
            await page.fill("input[data-test='maxPrice']", str(max_price))
            await page.keyboard.press("Enter")

            await page.click("button[data-test='radiusDropdown-toggle']")
            radius_selector = f"li[data-test='radius-{str(radius).replace('.', '-')}-miles']"
            if await page.locator(radius_selector).count():
                await page.click(radius_selector)

            await page.wait_for_selector(".propertyCard-wrapper", timeout=15000)

            cards = await page.locator(".propertyCard-wrapper").all()
            results = []

            for card in cards:
                title = await card.locator("[data-test='property-header']").text_content()
                price = await card.locator(".propertyCard-priceValue").text_content()
                link = await card.locator("a").first.get_attribute("href")
                image = await card.locator("img").first.get_attribute("src")
                results.append({
                    "title": title.strip() if title else "N/A",
                    "price": price.strip() if price else "N/A",
                    "link": f"https://www.rightmove.co.uk{link}" if link else "N/A",
                    "image": image if image else ""
                })

            await browser.close()
            return results

    except Exception as e:
        return {"error": str(e)}