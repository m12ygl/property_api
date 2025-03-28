
from fastapi import FastAPI, Query
from typing import Optional
from playwright.async_api import async_playwright
import subprocess
import uvicorn

# Ensure Chromium is installed
subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "UK Property Scout is live."}

@app.get("/search-properties")
async def search_properties(
    town: str = Query(..., description="The town to search properties in."),
    max_price: Optional[int] = Query(None, description="Maximum price filter."),
    radius: float = Query(0.25, ge=0.25, description="Search radius in miles (min 0.25).")
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Step 1: Convert town to locationIdentifier via manual search
        search_url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E{town}&radius={radius}&propertyTypes=&mustHave=&dontShow=&furnishTypes=&keywords="
        await page.goto(search_url)

        try:
            await page.wait_for_selector(".propertyCard-wrapper", timeout=30000)
        except:
            await browser.close()
            return {"error": "Timeout waiting for properties."}

        cards = await page.query_selector_all(".propertyCard-wrapper")
        results = []

        for card in cards[:5]:  # Limit to first 5 results
            try:
                title = await card.query_selector_eval("span[data-test='property-title']", "el => el.textContent") or "No title"
                price = await card.query_selector_eval("div[data-test='property-card-price']", "el => el.textContent") or "No price"
                link_el = await card.query_selector("a[data-test='property-card-link']")
                link = "https://www.rightmove.co.uk" + await link_el.get_attribute("href") if link_el else "No link"

                results.append({
                    "title": title.strip(),
                    "price": price.strip(),
                    "url": link
                })
            except:
                continue

        await browser.close()
        return results
