import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base_scraper import BaseScraper, PriceResult

SESSION_FILE   = Path("data/ica_session.json")
FALLBACK_STORE = "https://handlaprivatkund.ica.se/stores/1003408"


class ICAScraper(BaseScraper):

    def __init__(self):
        super().__init__("ica")
        self._pw      = None
        self._browser = None
        self._ctx     = None
        self._page    = None
        self._ready   = False

    def _session_exists(self) -> bool:
        return SESSION_FILE.exists()

    def _store_url(self) -> str:
        if not self._session_exists():
            return FALLBACK_STORE
        data = json.loads(SESSION_FILE.read_text())
        return data.get("store_url", FALLBACK_STORE)

    def _start(self):
        if self._ready:
            return
        if not self._session_exists():
            return

        session       = json.loads(SESSION_FILE.read_text())
        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._ctx     = self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="sv-SE",
            storage_state=session,
        )
        self._page = self._ctx.new_page()
        try:
            # Gå till butikssidan och vänta på att sökfältet syns
            self._page.goto(self._store_url(), timeout=25000, wait_until="networkidle")
            self._page.wait_for_selector('input[placeholder="Sök produkt"]', timeout=10000)
            self._ready = True
        except Exception as e:
            print(f"ICA start fel: {e}")

    def stop(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._browser = None
        self._pw      = None
        self._ctx     = None
        self._page    = None
        self._ready   = False

    def search(self, query: str) -> list[dict]:
        self._start()
        if not self._ready or not self._page:
            return []

        products = []

        def on_resp(r):
            if r.status == 200 and "json" in r.headers.get("content-type", ""):
                if "product-pages" in r.url:
                    try:
                        body = r.json()
                        for g in body.get("productGroups", []):
                            # v6 API använder decoratedProducts
                            for dp in g.get("decoratedProducts", []):
                                prod = dp.get("product", dp)
                                if prod.get("name"):
                                    products.append(prod)
                    except Exception:
                        pass

        self._page.on("response", on_resp)
        try:
            search_input = self._page.locator('input[placeholder="Sök produkt"]').first
            search_input.click()
            self._page.keyboard.press("Control+A")
            self._page.keyboard.press("Backspace")
            search_input.type(query, delay=50)
            self._page.keyboard.press("Enter")
            self._page.wait_for_timeout(5000)
        except Exception as e:
            print(f"ICA sökfel: {e}")
        finally:
            self._page.remove_listener("response", on_resp)

        return products

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        if not self._session_exists():
            return None
        results = self.search(product_name)
        if not results:
            return None

        product   = results[0]
        price_obj = product.get("price", {})
        price     = float(price_obj.get("amount", 0)) if isinstance(price_obj, dict) else None
        if not price:
            return None

        return PriceResult(
            product_id=product_id,
            product_name=product.get("name", product_name),
            store="ica",
            price=price,
            unit="st",
            offer="",
        )
