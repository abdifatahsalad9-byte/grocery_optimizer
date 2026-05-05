"""Gemensam logik för alla butikssidor."""
import base64
import json
import re
import requests
from pathlib import Path

import streamlit as st

PRODUCTS_FILE = Path("data/products.json")
IMAGES_DIR    = Path("static/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
}


def load_products() -> dict:
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_products(data: dict):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_id(name: str) -> str:
    replacements = {"å":"a","ä":"a","ö":"o","é":"e"," ":"_",
                    "/":"_","-":"_","&":"","%":"","(":"",")":""}
    result = name.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return re.sub(r"_+", "_", "".join(c for c in result if c.isalnum() or c == "_")).strip("_")[:30]


def download_image(url: str, pid: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        path = IMAGES_DIR / f"{pid}.jpg"
        path.write_bytes(r.content)
        return str(path)
    except Exception:
        return None


def img_tag(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        b64 = base64.b64encode(r.content).decode()
        return f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;height:110px;object-fit:contain"/>'
    except Exception:
        return '<div style="height:110px;display:flex;align-items:center;justify-content:center;color:#aaa">📦</div>'


def already_exists(pid: str) -> bool:
    data = load_products()
    return any(
        p["id"] == pid
        for prods in data["categories"].values()
        for p in prods
    )


def import_product(name: str, pid: str, emoji: str, category: str, image_url: str | None):
    data = load_products()
    if category not in data["categories"]:
        data["categories"][category] = []

    image_path = download_image(image_url, pid) if image_url else None
    product = {"id": pid, "name": name, "emoji": emoji, "unit": "förp"}
    if image_path:
        product["image"] = image_path

    data["categories"][category].append(product)
    save_products(data)


def render_product_grid(products: list[dict], store_emoji: str):
    """Visar ett rutnät med produkter och importknappar."""
    data       = load_products()
    categories = list(data["categories"].keys())
    emojis     = ["🍗","🥩","🐟","🥛","🧈","🥚","🧀","🍶","🥑","🍌","🍋",
                  "🍅","🥒","🫑","🥬","🥔","🧅","🌽","🥝","👶","🍼","🥣",
                  "🍝","🌾","🫙","🥫","🍞","🧴","🧻","🧽","🍦","🍟","🍫"]

    cols_per_row = 3
    for row_start in range(0, len(products), cols_per_row):
        row   = products[row_start : row_start + cols_per_row]
        cols  = st.columns(cols_per_row)
        for j, prod in enumerate(row):
            idx     = row_start + j          # unikt index för varje produkt
            pid     = make_id(prod["name"])
            exists  = already_exists(pid)
            img_url = prod.get("image_url")
            price   = prod.get("price", 0)
            # Unikt prefix för alla widget-nycklar
            k = f"{store_emoji}_{idx}"

            with cols[j]:
                if img_url:
                    st.markdown(img_tag(img_url), unsafe_allow_html=True)

                st.markdown(f"**{prod['name']}**")
                st.markdown(f"<span style='color:#e3000b;font-weight:700'>{price:.2f} kr</span>",
                            unsafe_allow_html=True)

                if exists:
                    st.success("✅ Finns redan")
                else:
                    with st.expander("➕ Importera"):
                        cat = st.selectbox("Kategori", categories + ["➕ Ny"],
                                           key=f"cat_{k}")
                        if cat == "➕ Ny":
                            cat = st.text_input("Ny kategori", key=f"newcat_{k}")
                        emoji = st.selectbox("Emoji", emojis, key=f"emo_{k}")

                        if st.button("Importera", key=f"imp_{k}",
                                     type="primary", use_container_width=True):
                            if cat:
                                import_product(prod["name"], pid, emoji, cat, img_url)
                                st.success(f"✅ {prod['name']} importerad!")
                                st.rerun()
