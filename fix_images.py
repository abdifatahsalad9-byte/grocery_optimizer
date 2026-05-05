"""
Kollar igenom alla produktbilder och fixar de som är fel.
Väljer bästa träffen från Willys sökning baserat på namnmatchning.
"""
import json
import time
import requests
from pathlib import Path

PRODUCTS_FILE = Path("data/products.json")
IMAGES_DIR    = Path("static/images")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.willys.se/",
}

# Manuella sökord för varor som är svåra att hitta automatiskt
CUSTOM_QUERIES = {
    "smor":            "Arla smör 500g",
    "agg":             "ägg 12-pack frigående",
    "min_yoghurt":     "min yoghurt jordgubb banan",
    "rapsolja":        "rapsolja 1 liter",
    "fusilli":         "fusilli pasta 500g",
    "citron_pressad":  "pressad citron flaska",
    "taco_spice":      "taco krydda",
    "orientbrod":      "pitabröd",
    "pappkasse":       "pappkasse mat",
    "dreamlengths_balsam": "balsam dreamlengths",
}


def normalize(text: str) -> str:
    return text.lower().replace("å","a").replace("ä","a").replace("ö","o")


def score_match(query: str, result_name: str) -> int:
    """Hur bra stämmer sökresultatet med det vi letar efter."""
    q_words = set(normalize(query).split())
    r_words = set(normalize(result_name).split())
    return len(q_words & r_words)


def search_willys(query: str) -> list[dict]:
    url = f"https://www.willys.se/search?q={requests.utils.quote(query)}&searchType=PRODUCT"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []


def best_match(results: list[dict], query: str) -> dict | None:
    if not results:
        return None
    scored = [(score_match(query, p.get("name", "")), p) for p in results[:8]]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    if best_score == 0:
        return results[0]  # Ta första om inga ord matchar
    return best


def download_image(url: str, path: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        path.write_bytes(r.content)
        return True
    except Exception:
        return False


def main():
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        products_data = json.load(f)

    all_products = [
        p
        for products in products_data["categories"].values()
        for p in products
        if p.get("image")
    ]

    fixed   = 0
    skipped = 0

    for i, product in enumerate(all_products, 1):
        pid   = product["id"]
        name  = product["name"]
        query = CUSTOM_QUERIES.get(pid, name)
        dest  = Path(product["image"])

        print(f"[{i}/{len(all_products)}] {name}", end=" ... ", flush=True)

        results = search_willys(query)
        match   = best_match(results, query)

        if not match:
            print("hittades inte")
            skipped += 1
            time.sleep(0.4)
            continue

        image_url = match.get("image", {}).get("url")
        if not image_url:
            print("ingen bild")
            skipped += 1
            time.sleep(0.4)
            continue

        ok = download_image(image_url, dest)
        if ok:
            print(f"✓  ({match.get('name')})")
            fixed += 1
        else:
            print("✗ nedladdning misslyckades")
            skipped += 1

        time.sleep(0.4)

    print(f"\n✅ Klart! {fixed} bilder uppdaterade, {skipped} misslyckades.")


if __name__ == "__main__":
    main()
