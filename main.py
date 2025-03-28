import subprocess
subprocess.run(["playwright", "install", "chromium"])

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

app = FastAPI()

@app.get("/search-properties")
async def search_properties(town: str = Query(..., description="Town to search in")):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.rightmove.co.uk/", timeout=60000)

            # Ensure the input is present before trying to type
            await page.wait_for_selector("input#searchLocation", timeout=15000)
            await page.fill("input#searchLocation", town)

            # Wait for the autocomplete dropdown and select the first item
            await page.wait_for_selector(".autoCompleteItem", timeout=10000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")

            # Wait for submit button and click
            await page.wait_for_selector("button[data-test='submit-button']", timeout=10000)
            await page.click("button[data-test='submit-button']")

            await page.wait_for_selector(".propertyCard-wrapper", timeout=30000)
            properties = await page.query_selector_all(".propertyCard-wrapper")

            results = []
            for prop in properties[:10]:
                title = await prop.inner_text() if prop else "N/A"
                link_element = await prop.query_selector("a")
                link = await link_element.get_attribute("href") if link_element else "#"
                results.append({
                    "title": title.strip().split("\n")[0],
                    "url": f"https://www.rightmove.co.uk{link}" if link else "N/A"
                })

            await browser.close()
            return results

    except PlaywrightTimeoutError as e:
        return JSONResponse(status_code=500, content={"error": f"Timeout: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/view-source", response_class=HTMLResponse)
async def view_source(town: str = Query(..., description="Town to search in")):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.rightmove.co.uk/", timeout=60000)

            await page.wait_for_selector("input#searchLocation", timeout=15000)
            await page.fill("input#searchLocation", town)
            await page.wait_for_selector(".autoCompleteItem", timeout=10000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.wait_for_selector("button[data-test='submit-button']", timeout=10000)
            await page.click("button[data-test='submit-button']")

            await page.wait_for_selector("body", timeout=15000)
            content = await page.content()
            await browser.close()
            return HTMLResponse(content=content)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})