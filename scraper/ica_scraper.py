import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base_scraper import BaseScraper, PriceResult

SESSION_FILE = Path("data/ica_session.json")
SEARCH_URL   = "https://handla.ica.se/handla/search?q={query}"


class ICAScraper(BaseScraper):

    def __init__(self):
        super().__init__("ica")
        self._pw      = None
        self._browser = None
        self._ctx     = None

    def _session_exists(self) -> bool:
        return SESSION_FILE.exists()

    def _start(self):
        if self._browser:
            return
        if not self._session_exists():
            raise RuntimeError("ICA-session saknas. Kör python3 ica_login.py först.")

        session = json.loads(SESSION_FILE.read_text())
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._ctx = self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="sv-SE",
            storage_state=session,
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
                if r.status == 200 and "json" in r.headers.get("content-type", ""):
                    url = r.url.lower()
                    if any(x in url for x in ["search", "product", "artikel"]):
                        try:
                            body = r.json()
                            # Försök hitta produktlista i olika format
                            items = (
                                body.get("products") or
                                body.get("items") or
                                body.get("results", {}).get("items") or
                                (body if isinstance(body, list) else [])
                            )
                            if items:
                                results.extend(items if isinstance(items, list) else [])
                        except Exception:
                            pass
            page.on("response", on_resp)
            page.goto(SEARCH_URL.format(query=query), timeout=25000, wait_until="networkidle")
            page.wait_for_timeout(3000)
        except PWTimeout:
            pass
        except Exception:
            pass
        finally:
            page.close()
        return results

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        if not self._session_exists():
            return None
        results = self.search(product_name)
        if not results:
            return None
        product = results[0]

        # ICA använder olika prisfält beroende på produkttyp
        price = (
            product.get("price") or
            product.get("priceValue") or
            product.get("currentPrice") or
            product.get("salesPrice") or
            (product.get("pricing", {}) or {}).get("price")
        )
        if price is None:
            return None

        promotions = product.get("promotions") or product.get("offers") or []
        offer = promotions[0].get("description", "") if promotions else ""

        return PriceResult(
            product_id=product_id,
            product_name=product.get("name", product_name),
            store="ica",
            price=float(price),
            unit=product.get("unit", "st"),
            offer=offer,
        )
