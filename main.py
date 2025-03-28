import subprocess
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright

subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/search-properties")
async def search_properties(town: str = Query(..., description="Town name to search properties in")):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            url = f"https://www.rightmove.co.uk/property-for-sale/{town}.html"
            await page.goto(url, timeout=60000)
            await page.wait_for_selector(".propertyCard-wrapper", timeout=30000)

            property_cards = await page.locator(".propertyCard-wrapper").all()
            properties = []

            for card in property_cards[:10]:
                title = await card.locator(".propertyCard-title").inner_text() if await card.locator(".propertyCard-title").count() else "No title"
                price = await card.locator(".propertyCard-priceValue").inner_text() if await card.locator(".propertyCard-priceValue").count() else "No price"
                location = await card.locator(".propertyCard-address").inner_text() if await card.locator(".propertyCard-address").count() else "No location"
                link = await card.locator("a").get_attribute("href") if await card.locator("a").count() else None
                full_link = f"https://www.rightmove.co.uk{link}" if link else None

                properties.append({
                    "title": title.strip(),
                    "price": price.strip(),
                    "location": location.strip(),
                    "link": full_link
                })

            await browser.close()
            return {"results": properties}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})