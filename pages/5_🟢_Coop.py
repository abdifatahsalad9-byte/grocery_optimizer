import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import streamlit as st
from pages.store_page_helper import render_product_grid

st.set_page_config(page_title="Coop", page_icon="🟢", layout="wide")

COOP_API  = "https://external.api.coop.se/personalization/search/products?api-version=v1&store=251300&groups=CUSTOMER_PRIVATE&device=desktop&direct=true"
COOP_KEY  = "3becf0ce306f41a1ae94077c16798187"
HEADERS   = {
    "User-Agent":               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":                   "application/json, text/plain, */*",
    "Content-Type":             "application/json",
    "ocp-apim-subscription-key": COOP_KEY,
    "Referer":                  "https://www.coop.se/",
    "Origin":                   "https://www.coop.se",
}

st.title("🟢 Coop — Importera produkter")
st.caption("Sök på Coop och importera varor direkt till din app")

query = st.text_input("🔍 Sök produkt", placeholder="t.ex. havregryn, yoghurt, blöjor...")

if query:
    with st.spinner(f"Söker efter '{query}' på Coop..."):
        body = {"query": query, "resultsOptions": {"skip": 0, "take": 24, "sortBy": [], "facets": []}}
        try:
            r     = requests.post(COOP_API, headers=HEADERS, json=body, timeout=10)
            items = r.json().get("results", {}).get("items", []) if r.status_code == 200 else []
        except Exception:
            items = []

    if not items:
        st.warning("Inga produkter hittades.")
    else:
        st.markdown(f"**{len(items)} produkter hittades på Coop:**")
        products = []
        for item in items:
            price = item.get("salesPriceData", {}).get("b2cPrice")
            if not price or float(price) > 500:
                continue
            products.append({
                "name":      item.get("name", ""),
                "price":     float(price),
                "image_url": item.get("imageUrl"),
            })
        render_product_grid(products, "coop")
