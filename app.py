import json
from pathlib import Path

import streamlit as st
import pandas as pd

from scraper.mock_scraper import MockScraper

# ── Konfiguration ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"

STORES = {
    "🟡 Willys": MockScraper("willys"),
    "🔴 ICA":    MockScraper("ica"),
}

# ── Hjälpfunktioner ────────────────────────────────────────────────────────────

def load_products() -> dict:
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def init_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = {}  # {product_id: {"name": ..., "qty": ..., "emoji": ...}}


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


def compare_prices() -> pd.DataFrame:
    cart_products = [
        {"id": pid, "name": info["name"]}
        for pid, info in st.session_state.cart.items()
    ]
    rows = []
    store_totals: dict[str, float] = {name: 0.0 for name in STORES}

    for pid, info in st.session_state.cart.items():
        row = {"Vara": f"{info['emoji']} {info['name']}", "Antal": info["qty"]}
        for store_name, scraper in STORES.items():
            result = scraper.get_price(pid, info["name"])
            if result:
                unit_price = result.price
                total = unit_price * info["qty"]
                store_totals[store_name] += total
                label = f"{unit_price:.2f} kr"
                if result.offer:
                    label += f"\n💥 {result.offer}"
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
  .product-btn button {
    height: 80px !important;
    font-size: 1rem !important;
    border-radius: 12px !important;
    width: 100% !important;
  }
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

# ── Sidopanel: Kundkorg ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 Din korg")

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

    df, store_totals = compare_prices()

    # Visa vinnande butik
    best_store = min(store_totals, key=store_totals.get)
    worst_store = max(store_totals, key=store_totals.get)
    savings = store_totals[worst_store] - store_totals[best_store]

    st.success(
        f"✅ **Handla på {best_store}** – du sparar **{savings:.2f} kr** "
        f"jämfört med {worst_store}!"
    )

    col1, col2 = st.columns(2)
    for i, (store_name, total) in enumerate(store_totals.items()):
        target = col1 if i == 0 else col2
        is_best = store_name == best_store
        with target:
            st.metric(
                label=store_name,
                value=f"{total:.2f} kr",
                delta=f"{'Billigast! 🏆' if is_best else f'+{total - store_totals[best_store]:.2f} kr'}",
                delta_color="normal" if is_best else "inverse",
            )

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
    )

    if st.button("❌ Stäng jämförelsen"):
        st.session_state.show_comparison = False
        st.rerun()
