import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import streamlit as st
from pages.store_page_helper import render_product_grid

st.set_page_config(page_title="Willys", page_icon="🟡", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.willys.se/",
}

st.title("🟡 Willys — Importera produkter")
st.caption("Sök på Willys och importera varor direkt till din app")

query = st.text_input("🔍 Sök produkt", placeholder="t.ex. havregryn, yoghurt, blöjor...")

if query:
    with st.spinner(f"Söker efter '{query}' på Willys..."):
        url = f"https://www.willys.se/search?q={requests.utils.quote(query)}&searchType=PRODUCT"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            results = r.json().get("results", [])
        except Exception:
            results = []

    if not results:
        st.warning("Inga produkter hittades.")
    else:
        st.markdown(f"**{len(results)} produkter hittades på Willys:**")

        products = []
        for item in results[:18]:
            price = item.get("priceValue")
            if price is None:
                continue
            img = item.get("image", {})
            products.append({
                "name":      item.get("name", ""),
                "price":     float(price),
                "image_url": img.get("url") if img else None,
            })

        render_product_grid(products, "willys")
