import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from .base_scraper import BaseScraper, PriceResult

SESSION_FILE   = Path("data/ica_session.json")
FALLBACK_STORE = "https://handlaprivatkund.ica.se/stores/1003408"

ICA_QUERIES = {
    "kycklingfile":       "kycklingfilé",
    "kycklingkebab":      "kycklingkebab",
    "kycklingleårfile":   "kycklinglårfilé",
    "kycklinginnerfile":  "kycklinginnerfilé",
    "mjolk":              "standardmjölk",
    "smor":               "smör 500g",
    "agg":                "ägg frigående",
    "grekisk_yoghurt":    "grekisk yoghurt",
    "yoghurt":            "yoghurt naturell",
    "yoghurt_vanilj":     "yoghurt vanilj",
    "matgradde":          "matgrädde",
    "vispgradde":         "vispgrädde",
    "gradde":             "grädde",
    "graddfil":           "gräddfil",
    "avokado":            "avokado",
    "banan":              "banan eko",
    "citron":             "citron",
    "tomat_baby":         "tomat babyplommon",
    "gurka":              "gurka",
    "paprika":            "paprika mix",
    "isbergssallad":      "isbergssallad",
    "zucchini":           "zucchini",
    "potatis":            "potatis fast",
    "gul_lok":            "lök gul",
    "rod_lok":            "lök röd",
    "majskolv":           "majskolv",
    "blojor":             "blöjor touch",
    "nan_pro":            "nan pro",
    "fruktmums":          "fruktmums",
    "fruktgrot":          "fruktgröt",
    "pasta":              "penne rigate",
    "hamburgerbrod":      "hamburgerbröd",
    "polarvete":          "polarbröd vete",
    "lingongrova":        "lingongrova",
    "diskmedel":          "diskmedel",
    "hushallspapper":     "hushållspapper",
    "toapapper":          "toapapper",
}


class ICAScraper(BaseScraper):

    def __init__(self):
        super().__init__("ica")
        self._pw      = None
        self._browser = None
        self._ctx     = None
        self._page    = None   # återanvänds mellan sökningar
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
        # Öppna butikssidan EN gång och behåll den öppen
        self._page = self._ctx.new_page()
        try:
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
                            for dp in g.get("decoratedProducts", []):
                                prod = dp.get("product", dp)
                                if prod.get("name"):
                                    products.append(prod)
                    except Exception:
                        pass

        self._page.on("response", on_resp)
        try:
            # Rensa sökfältet och skriv ny sökning
            search_input = self._page.locator('input[placeholder="Sök produkt"]').first
            search_input.click()
            self._page.keyboard.press("Control+A")
            self._page.keyboard.press("Backspace")
            search_input.type(query, delay=30)
            self._page.keyboard.press("Enter")
            # Vänta på att sökresultaten laddas
            self._page.wait_for_timeout(4000)
        except Exception as e:
            print(f"ICA sökfel ({query}): {e}")
        finally:
            self._page.remove_listener("response", on_resp)

        # Om inga träffar — navigera tillbaka till butikssidan och försök igen
        if not products:
            try:
                self._page.goto(self._store_url(), timeout=20000, wait_until="networkidle")
                self._page.wait_for_selector('input[placeholder="Sök produkt"]', timeout=8000)
                self._page.on("response", on_resp)
                search_input = self._page.locator('input[placeholder="Sök produkt"]').first
                search_input.click()
                search_input.type(query, delay=30)
                self._page.keyboard.press("Enter")
                self._page.wait_for_timeout(4000)
            except Exception:
                pass
            finally:
                try:
                    self._page.remove_listener("response", on_resp)
                except Exception:
                    pass

        return products

    # Ord som tyder på marinerat/specialvariant — undviks om de inte finns i sökordet
    _AVOID = {"bbq", "marinerad", "kryddad", "grillad", "färdig", "fryst", "rökt"}

    def _best_match(self, results: list[dict], query: str) -> dict | None:
        query_words  = set(query.lower().split())
        query_avoid  = self._AVOID - query_words  # undvik dessa om de inte efterfrågas
        best, best_score = None, -1

        for prod in results:
            name       = (prod.get("name") or "").lower()
            name_words = set(name.split())
            match  = sum(1 for w in query_words if w in name)
            # Sänk poängen om produkten innehåller undvikta ord
            penalty = sum(1 for w in query_avoid if w in name)
            score   = match - penalty * 0.5
            if score > best_score:
                best_score = score
                best = prod

        return best if best and best_score > 0 else (results[0] if results else None)

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        if not self._session_exists():
            return None

        query   = ICA_QUERIES.get(product_id, product_name)
        results = self.search(query)
        if not results:
            return None

        product   = self._best_match(results, query)
        if not product:
            return None

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
