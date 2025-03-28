
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import asyncio
import requests

app = FastAPI()

def get_location_identifier_from_town(town: str):
    search_url = f"https://www.rightmove.co.uk/typeAhead/uknostreet/{town.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        return None

    data = response.json()
    if not data:
        return None

    return data[0]["locationIdentifier"]

@app.get("/search-properties")
async def search_properties(town: str = Query(...), max_price: int = Query(500000)):
    location_identifier = get_location_identifier_from_town(town)
    if not location_identifier:
        return JSONResponse(status_code=400, content={"error": f"Could not find a locationIdentifier for '{town}'"})

    url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier={location_identifier}&maxPrice={max_price}&sortType=6&propertyTypes=&includeSSTC=false&mustHave=&dontShow=&furnishTypes=&keywords="

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        try:
            await page.wait_for_selector(".propertyCard-wrapper", timeout=30000)
        except:
            await browser.close()
            return JSONResponse(status_code=500, content={"error": "Timeout waiting for properties: Page.wait_for_selector: Timeout 30000ms exceeded.\nCall log:\n  - waiting for locator(\".propertyCard-wrapper\") to be visible\n"})

        properties = await page.query_selector_all(".propertyCard-wrapper")
        results = []

        for property_card in properties[:10]:  # Limit to top 10 results
            title = await property_card.inner_text() if property_card else "No title"
            results.append({
                "summary": title.strip().replace("\n", " ")
            })

        await browser.close()
        return results
