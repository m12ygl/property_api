import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio

# ✅ Ensure Chromium is installed at runtime
subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "UK Property Search API is running."}

@app.get("/search-properties")
async def search_properties(town: str = Query(..., description="Town name, e.g., Harrow")):
    url = f"https://www.rightmove.co.uk/property-for-sale/{town}.html"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)

            await page.wait_for_selector(".propertyCard-wrapper", timeout=30000)

            properties = await page.locator(".propertyCard-wrapper").all()
            results = []

            for property_card in properties[:10]:
                try:
                    title = await property_card.locator(".propertyCard-title").inner_text()
                except:
                    title = "No title found"

                try:
                    price = await property_card.locator(".propertyCard-priceValue").inner_text()
                except:
                    price = "No price listed"

                try:
                    address = await property_card.locator(".propertyCard-address").inner_text()
                except:
                    address = "No address found"

                results.append({
                    "title": title.strip(),
                    "price": price.strip(),
                    "address": address.strip()
                })

            await browser.close()
            return results

    except PlaywrightTimeout:
        return JSONResponse(status_code=504, content={"error": "Timeout waiting for property cards."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})