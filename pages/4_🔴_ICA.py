import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from pages.store_page_helper import render_product_grid

st.set_page_config(page_title="ICA", page_icon="🔴", layout="wide")

SESSION_FILE = Path("data/ica_session.json")

st.title("🔴 ICA — Importera produkter")
st.caption("Sök på ICA och importera varor direkt till din app")

if not SESSION_FILE.exists():
    st.error("ICA-session saknas. Kör `python3 ica_login.py` först för att logga in.")
    st.stop()

query = st.text_input("🔍 Sök produkt", placeholder="t.ex. havregryn, yoghurt, blöjor...")

if query:
    with st.spinner(f"Söker efter '{query}' på ICA..."):
        from scraper.ica_scraper import ICAScraper
        scraper = ICAScraper()
        try:
            results = scraper.search(query)
        except Exception as e:
            results = []
            st.error(f"Fel: {e}")
        finally:
            scraper.stop()

    if not results:
        st.warning("Inga produkter hittades. Testa ett kortare sökord.")
    else:
        st.markdown(f"**{len(results)} produkter hittades på ICA:**")

        products = []
        for item in results[:18]:
            price_obj = item.get("price", {})
            price     = float(price_obj.get("amount", 0)) if isinstance(price_obj, dict) else None
            if not price:
                continue
            # ICA har bilder via separat URL-mönster
            prod_id = item.get("retailerProductId") or item.get("productId", "")
            products.append({
                "name":      item.get("name", ""),
                "price":     price,
                "image_url": None,  # ICA-bilder kräver autentisering
            })

        render_product_grid(products, "ica")
