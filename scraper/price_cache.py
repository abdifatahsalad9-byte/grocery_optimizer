import json
from datetime import datetime, timedelta
from pathlib import Path

CACHE_FILE = Path(__file__).parent.parent / "data" / "price_cache.json"
CACHE_MAX_AGE = timedelta(hours=24)


def cache_age() -> timedelta | None:
    """Returnerar hur gammal cachen är, eller None om den inte finns."""
    if not CACHE_FILE.exists():
        return None
    with open(CACHE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    updated_at = datetime.fromisoformat(data["updated_at"])
    return datetime.now() - updated_at


def load_cache() -> dict | None:
    """Laddar cache om den finns och är färsk (< 24h). Annars None."""
    age = cache_age()
    if age is None or age > CACHE_MAX_AGE:
        return None
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)["prices"]


def save_cache(prices: dict):
    data = {
        "updated_at": datetime.now().isoformat(),
        "prices": prices,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_prices(stores: dict, products_data: dict) -> dict:
    """Hämtar priser från alla butiker och sparar i cache."""
    prices = {}
    all_products = [
        p for prods in products_data["categories"].values() for p in prods
    ]

    for store_key, scraper in stores.items():
        print(f"Hämtar priser: {store_key}...")
        prices[store_key] = {}
        for product in all_products:
            try:
                result = scraper.get_price(product["id"], product["name"])
                if result:
                    prices[store_key][product["id"]] = {
                        "price":   result.price,
                        "offer":   result.offer,
                        "is_real": result.is_real,
                    }
            except Exception:
                pass

        # Stäng Playwright-scrapers efter varje butik
        if hasattr(scraper, "stop"):
            scraper.stop()

    save_cache(prices)
    return prices


def last_updated_text() -> str:
    age = cache_age()
    if age is None:
        return "Priser ej hämtade än"
    minutes = int(age.total_seconds() // 60)
    if minutes < 60:
        return f"Uppdaterat för {minutes} min sedan"
    hours = minutes // 60
    return f"Uppdaterat för {hours} tim sedan"
