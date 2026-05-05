import requests
from .base_scraper import BaseScraper, PriceResult

SEARCH_URL = "https://www.hemkop.se/search?q={query}&searchType=PRODUCT"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.hemkop.se/",
}


class HemkopScraper(BaseScraper):

    def __init__(self):
        super().__init__("hemkop")
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search(self, query: str) -> list[dict]:
        url = SEARCH_URL.format(query=requests.utils.quote(query))
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            return r.json().get("results", [])
        except Exception:
            return []

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        results = self.search(product_name)
        if not results:
            return None
        product = results[0]
        price = product.get("priceValue")
        if price is None:
            return None
        promotions = product.get("potentialPromotions", [])
        offer = promotions[0].get("header", "") if promotions else ""
        return PriceResult(
            product_id=product_id,
            product_name=product.get("name", product_name),
            store="hemkop",
            price=float(price),
            unit=product.get("priceUnit", "st"),
            offer=offer,
        )
