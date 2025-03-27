
from fastapi import FastAPI, Query
from typing import Optional
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI()

@app.get("/search-properties")
def get_rightmove_listings(location: str = "London", max_price: Optional[int] = None):
    # Encode location and construct search URL
    location_encoded = urllib.parse.quote(location)
    base_url = "https://www.rightmove.co.uk/property-for-sale/find.html"
    query_params = f"?locationIdentifier=OUTCODE%5E{location_encoded}&minBedrooms=1&radius=10&sortType=6&index=0"

    if max_price:
        query_params += f"&maxPrice={max_price}"

    url = base_url + query_params
    headers = {"User-Agent": "Mozilla/5.0"}
    listings = []

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        properties = soup.find_all("div", class_="l-searchResult is-list")

        for prop in properties[:10]:  # limit to 10
            title_tag = prop.find("h2", class_="propertyCard-title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            price_tag = prop.find("div", class_="propertyCard-priceValue")
            price = price_tag.get_text(strip=True) if price_tag else "No price"

            link_tag = prop.find("a", class_="propertyCard-link")
            link = "https://www.rightmove.co.uk" + link_tag['href'] if link_tag else "#"

            image_tag = prop.find("img", class_="propertyCard-img")
            image = image_tag['src'] if image_tag and 'src' in image_tag.attrs else ""

            summary = f"• {title}\n• Price: {price}\n• Link: {link}"

            listings.append({
                "title": title,
                "price": price,
                "url": link,
                "image": image,
                "summary": summary
            })

    except Exception as e:
        return {"error": str(e)}

    return listings
