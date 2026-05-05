"""
Willys-skraper – redo att byggas ut med riktig web-scraping.

Kräver: pip install requests beautifulsoup4 playwright
Notera: Willys blockerar ibland automatiska förfrågningar.
Alternativ: Använd Matpriskollen API om tillgängligt.
"""
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, PriceResult


class WillysScraper(BaseScraper):
    BASE_URL = "https://www.willys.se/search?q={query}&type=RECIPE_CONTEXT"

    def __init__(self):
        super().__init__("Willys")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; GroceryOptimizer/1.0)"
        })

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        # TODO: Implementera riktig scraping här
        # url = self.BASE_URL.format(query=product_name)
        # response = self.session.get(url, timeout=10)
        # soup = BeautifulSoup(response.text, "html.parser")
        # price_tag = soup.select_one(".price")  # Anpassa CSS-selector
        # ...
        raise NotImplementedError("WillysScraper är inte implementerad ännu – använd MockScraper")
