
import subprocess
import uvicorn
from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import asyncio

subprocess.run(["playwright", "install", "chromium"])

app = FastAPI()

@app.get("/search-properties")
async def search_properties(town: str = Query(..., description="The town to search properties in")):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.rightmove.co.uk/")

            # Wait for and fill the search input
            await page.wait_for_selector("input#ta_searchInput", timeout=15000)
            await page.fill("input#ta_searchInput", town)
            await page.wait_for_timeout(1000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

            # Accept cookies if the popup appears
try:
    accept_button = await page.wait_for_selector("button#onetrust-accept-btn-handler", timeout=5000)
    await accept_button.click()
    print("Accepted cookie popup.")
except:
    print("No cookie popup detected.")

            # Click "For Sale" to start search
            await page.wait_for_selector("button:has-text('For sale')", timeout=5000)
            await page.click("button:has-text('For sale')")

            await page.wait_for_selector(".propertyCard-wrapper", timeout=15000)
            cards = await page.query_selector_all(".propertyCard-wrapper")

            results = []
            for card in cards:
                title = await card.inner_text()
                results.append({"text": title})

            await browser.close()
            return results

    except Exception as e:
        return {"error": str(e)}

@app.get("/view-source")
async def view_source(town: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.rightmove.co.uk/")
            await page.wait_for_selector("input#ta_searchInput", timeout=15000)
            await page.fill("input#ta_searchInput", town)
            await page.wait_for_timeout(1000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.wait_for_selector("button:has-text('For sale')", timeout=5000)
            await page.click("button:has-text('For sale')")
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            await browser.close()
            return {"html": content}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
