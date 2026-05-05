"""
Kör en gång för att ladda ner produktbilder från Willys.
Sparar bilderna i static/images/{product_id}.jpg

Användning:
    python3 download_images.py
"""
import json
import time
from pathlib import Path

import requests

from scraper.willys_scraper import WillysScraper

PRODUCTS_FILE = Path("data/products.json")
IMAGES_DIR    = Path("static/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def download_image(url: str, path: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"  Kunde inte ladda ner bild: {e}")
        return False


def main():
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        products_data = json.load(f)

    scraper = WillysScraper()
    image_map = {}
    total = sum(len(p) for p in products_data["categories"].values())
    count = 0

    for category, products in products_data["categories"].items():
        print(f"\n── {category} ──")
        for product in products:
            count += 1
            pid  = product["id"]
            name = product["name"]
            dest = IMAGES_DIR / f"{pid}.jpg"

            print(f"[{count}/{total}] {name}", end=" ... ", flush=True)

            if dest.exists():
                print("redan nedladdad ✓")
                image_map[pid] = str(dest)
                continue

            image_url = scraper.get_image_url(name)
            if image_url:
                ok = download_image(image_url, dest)
                if ok:
                    image_map[pid] = str(dest)
                    print("✓")
                else:
                    print("✗")
            else:
                print("hittades inte")

            time.sleep(0.5)  # Vänta lite mellan varje förfrågan

    # Spara bildsökvägar i products.json
    for category, products in products_data["categories"].items():
        for product in products:
            pid = product["id"]
            if pid in image_map:
                product["image"] = image_map[pid]

    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Klart! {len(image_map)}/{total} bilder nedladdade.")
    print("Starta om appen för att se bilderna.")


if __name__ == "__main__":
    main()
