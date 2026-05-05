import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base_scraper import BaseScraper, PriceResult

SEARCH_URL = "https://www.coop.se/handla/sok/?q={query}"


class CoopScraper(BaseScraper):

    def __init__(self):
        super().__init__("coop")
        self._pw = None
        self._browser = None
        self._ctx = None

    def _start(self):
        if self._browser:
            return
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._ctx = self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="sv-SE",
        )

    def stop(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._browser = None
        self._pw = None
        self._ctx = None

    def search(self, query: str) -> list[dict]:
        self._start()
        page = self._ctx.new_page()
        results = []
        try:
            def on_resp(r):
                if "personalization/search/products" in r.url and r.status == 200:
                    try:
                        data = r.json()
                        items = data.get("results", {}).get("items", [])
                        results.extend(items)
                    except Exception:
                        pass
            page.on("response", on_resp)
            page.goto(SEARCH_URL.format(query=query), timeout=25000, wait_until="networkidle")
        except PWTimeout:
            pass
        except Exception:
            pass
        finally:
            page.close()
        return results

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        results = self.search(product_name)
        if not results:
            return None
        product = results[0]
        price = product.get("salesPriceData", {}).get("b2cPrice")
        if price is None:
            return None
        return PriceResult(
            product_id=product_id,
            product_name=product.get("name", product_name),
            store="coop",
            price=float(price),
            unit="st",
            offer="",
        )
