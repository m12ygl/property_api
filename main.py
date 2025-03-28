from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Rightmove Property API is running 🚀"}

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

            # Force-remove the cookie overlay if it's still blocking interactions
            try:
                await page.evaluate("""
                    () => {
                        const el = document.getElementById('onetrust-consent-sdk');
                        if (el) el.remove();
                    }
                """)
                print("Forced removal of cookie overlay.")
            except Exception as e:
                print(f"No overlay removed: {e}")

            # Click "For Sale" to start search
            await page.wait_for_selector("button:has-text('For sale')", timeout=5000)
            await page.click("button:has-text('For sale')")

            await page.wait_for_selector(".propertyCard-wrapper", timeout=15000)
            property_cards = await page.query_selector_all(".propertyCard-wrapper")

            results = []
            for card in property_cards:
                title_el = await card.query_selector("h2")
                link_el = await card.query_selector("a")
                price_el = await card.query_selector(".propertyCard-priceValue")

                title = await title_el.inner_text() if title_el else "No title"
                link = await link_el.get_attribute("href") if link_el else "#"
                price = await price_el.inner_text() if price_el else "No price"

                results.append({
                    "title": title.strip(),
                    "price": price.strip(),
                    "url": f"https://www.rightmove.co.uk{link}"
                })

            await browser.close()
            return results
    except Exception as e:
        return {"error": str(e)}

@app.get("/view-source")
async def view_source(town: str = Query(..., description="The town to search properties in")):
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

            await page.wait_for_timeout(5000)
            content = await page.content()

            await browser.close()
            return {"html": content}
    except Exception as e:
        return {"error": str(e)}
