import json
from pathlib import Path

import streamlit as st
import pandas as pd

from scraper.mock_scraper import MockScraper
from scraper.price_cache import fetch_prices, load_cache, last_updated_text

# ── Konfiguration ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
STORES_FILE   = DATA_DIR / "stores.json"


def load_stores() -> dict:
    with open(STORES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {
        f"{s['emoji']} {s['name']}": MockScraper(s["id"])
        for s in data["stores"]
    }


def load_products() -> dict:
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        return json.load(f)


STORES = load_stores()


def get_prices(force_refresh: bool = False) -> dict:
    if not force_refresh:
        cached = load_cache()
        if cached:
            return cached
    return fetch_prices(STORES, load_products())


# ── Hjälpfunktioner ────────────────────────────────────────────────────────────

def init_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = {}


def add_to_cart(product: dict):
    pid = product["id"]
    if pid in st.session_state.cart:
        st.session_state.cart[pid]["qty"] += 1
    else:
        st.session_state.cart[pid] = {
            "name": product["name"],
            "qty": 1,
            "emoji": product["emoji"],
        }


def remove_from_cart(product_id: str):
    st.session_state.cart.pop(product_id, None)


def change_qty(product_id: str, delta: int):
    if product_id in st.session_state.cart:
        st.session_state.cart[product_id]["qty"] += delta
        if st.session_state.cart[product_id]["qty"] <= 0:
            remove_from_cart(product_id)


def compare_prices(prices: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    store_totals: dict[str, float] = {name: 0.0 for name in STORES}

    for pid, info in st.session_state.cart.items():
        row = {"Vara": f"{info['emoji']} {info['name']}", "Antal": info["qty"]}
        for store_name in STORES:
            store_prices = prices.get(store_name, {})
            if pid in store_prices:
                unit_price = store_prices[pid]["price"]
                offer      = store_prices[pid]["offer"]
                total      = unit_price * info["qty"]
                store_totals[store_name] += total
                label = f"{unit_price:.2f} kr"
                if offer:
                    label += f"\n💥 {offer}"
                row[store_name] = label
            else:
                row[store_name] = "—"
        rows.append(row)

    totals_row = {"Vara": "**TOTALT**", "Antal": ""}
    for store_name, total in store_totals.items():
        totals_row[store_name] = f"**{total:.2f} kr**"
    rows.append(totals_row)

    return pd.DataFrame(rows), store_totals


# ── Layout ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Matinköp",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .stButton button {
    border-radius: 10px;
  }
  div[data-testid="stSidebar"] .stButton button {
    font-size: 1.1rem;
  }
</style>
""", unsafe_allow_html=True)

init_cart()
products_data = load_products()

# Ladda priser (från cache om möjligt)
if "prices" not in st.session_state:
    st.session_state.prices = get_prices()

# ── Sidopanel: Kundkorg ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 Din korg")

    # Prisstatus + uppdateringsknapp
    st.caption(f"🕐 {last_updated_text()}")
    if st.button("🔄 Uppdatera priser", use_container_width=True):
        with st.spinner("Hämtar priser från alla butiker..."):
            st.session_state.prices = get_prices(force_refresh=True)
        st.success("Priser uppdaterade!")
        st.rerun()

    st.divider()

    if not st.session_state.cart:
        st.info("Korgen är tom.\nTryck på varor till höger för att lägga till.")
    else:
        for pid, info in list(st.session_state.cart.items()):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{info['emoji']} {info['name']}")
            with col2:
                st.write(f"×{info['qty']}")
            with col3:
                if st.button("🗑", key=f"del_{pid}"):
                    remove_from_cart(pid)
                    st.rerun()

        st.divider()
        if st.button("🗑️ Töm korgen", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()

        st.divider()
        if st.button("📊 Jämför priser", type="primary", use_container_width=True):
            st.session_state.show_comparison = True

# ── Huvudvy: Produktkatalog ────────────────────────────────────────────────────
st.title("🛒 Matinköp")
st.caption("Tryck på en vara för att lägga till den i korgen")

for category, products in products_data["categories"].items():
    st.subheader(category)
    cols = st.columns(5)
    for i, product in enumerate(products):
        in_cart = product["id"] in st.session_state.cart
        qty = st.session_state.cart.get(product["id"], {}).get("qty", 0)
        label = f"{product['emoji']}\n{product['name']}"
        if in_cart:
            label += f"\n✅ ×{qty}"

        with cols[i % 5]:
            if st.button(label, key=f"btn_{product['id']}", use_container_width=True):
                add_to_cart(product)
                st.rerun()

# ── Prisjämförelse ─────────────────────────────────────────────────────────────
if st.session_state.get("show_comparison") and st.session_state.cart:
    st.divider()
    st.header("📊 Prisjämförelse")

    df, store_totals = compare_prices(st.session_state.prices)

    best_store  = min(store_totals, key=store_totals.get)
    worst_store = max(store_totals, key=store_totals.get)
    savings     = store_totals[worst_store] - store_totals[best_store]

    st.success(
        f"✅ **Handla på {best_store}** – du sparar **{savings:.2f} kr** "
        f"jämfört med {worst_store}!"
    )

    cols = st.columns(len(STORES))
    for i, (store_name, total) in enumerate(store_totals.items()):
        is_best = store_name == best_store
        with cols[i]:
            st.metric(
                label=store_name,
                value=f"{total:.2f} kr",
                delta="Billigast! 🏆" if is_best else f"+{total - store_totals[best_store]:.2f} kr",
                delta_color="normal" if is_best else "inverse",
            )

    st.dataframe(df, hide_index=True, use_container_width=True)

    if st.button("❌ Stäng jämförelsen"):
        st.session_state.show_comparison = False
        st.rerun()
