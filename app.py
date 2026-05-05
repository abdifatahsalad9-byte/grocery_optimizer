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
  /* Produktknappar */
  .stButton button {
    border-radius: 12px;
  }

  /* Korgens varurad */
  .cart-item {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .cart-item-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #1a1a2e;
  }
  .cart-item-qty {
    background: #e8f4fd;
    color: #1565c0;
    border-radius: 20px;
    padding: 2px 10px;
    font-weight: 700;
    font-size: 0.85rem;
  }
  .cart-total-box {
    background: linear-gradient(135deg, #1565c0, #0d47a1);
    border-radius: 14px;
    padding: 14px 16px;
    color: white;
    text-align: center;
    margin: 10px 0;
  }
  .cart-total-label {
    font-size: 0.8rem;
    opacity: 0.85;
    margin-bottom: 2px;
  }
  .cart-total-amount {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 0.5px;
  }
  .cart-empty {
    text-align: center;
    padding: 30px 10px;
    color: #888;
  }
  .cart-empty-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
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
    st.markdown("## 🛒 Din korg")
    st.caption(f"🕐 {last_updated_text()}")

    if not st.session_state.cart:
        st.markdown("""
        <div class="cart-empty">
          <div class="cart-empty-icon">🛒</div>
          <div>Korgen är tom</div>
          <div style="font-size:0.8rem;margin-top:4px;color:#aaa">Tryck på varor för att lägga till</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Räkna ut korgtotal från Willys-priser
        willys_prices = st.session_state.prices.get("🟡 Willys", {})
        cart_total = sum(
            willys_prices.get(pid, {}).get("price", 0) * info["qty"]
            for pid, info in st.session_state.cart.items()
        )
        n_items = sum(info["qty"] for info in st.session_state.cart.values())

        # Total-box
        st.markdown(f"""
        <div class="cart-total-box">
          <div class="cart-total-label">{n_items} varor (Willys-pris)</div>
          <div class="cart-total-amount">{cart_total:.0f} kr</div>
        </div>
        """, unsafe_allow_html=True)

        # Varor i korgen
        all_products_flat = {
            p["id"]: p
            for prods in products_data["categories"].values()
            for p in prods
        }
        for pid, info in list(st.session_state.cart.items()):
            product    = all_products_flat.get(pid, {})
            image_path = product.get("image")

            col_img, col_name, col_minus, col_qty, col_plus = st.columns([1.2, 3.5, 0.8, 0.8, 0.8])
            with col_img:
                if image_path and Path(image_path).exists():
                    st.image(image_path, use_container_width=True)
                else:
                    st.markdown(f"<div style='font-size:1.8rem;text-align:center'>{info['emoji']}</div>", unsafe_allow_html=True)
            with col_name:
                st.markdown(f"<div class='cart-item-name' style='padding-top:8px'>{info['name']}</div>", unsafe_allow_html=True)
            with col_minus:
                if st.button("−", key=f"minus_{pid}"):
                    change_qty(pid, -1)
                    st.rerun()
            with col_qty:
                st.markdown(f"<div style='text-align:center;padding-top:6px;font-weight:700'>{info['qty']}</div>", unsafe_allow_html=True)
            with col_plus:
                if st.button("＋", key=f"plus_{pid}"):
                    change_qty(pid, 1)
                    st.rerun()

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Töm", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        with col_b:
            if st.button("🔄 Priser", use_container_width=True):
                with st.spinner("Hämtar..."):
                    st.session_state.prices = get_prices(force_refresh=True)
                st.rerun()

        st.button(
            "📊 Jämför priser i alla butiker",
            type="primary",
            use_container_width=True,
            on_click=lambda: st.session_state.update(show_comparison=True),
        )

# ── Huvudvy: Produktkatalog ────────────────────────────────────────────────────
st.title("🛒 Matinköp")
st.caption("Tryck på en vara för att lägga till den i korgen")

for category, products in products_data["categories"].items():
    st.subheader(category)
    cols = st.columns(5)
    for i, product in enumerate(products):
        in_cart = product["id"] in st.session_state.cart
        qty     = st.session_state.cart.get(product["id"], {}).get("qty", 0)
        label   = f"{product['emoji']} {product['name']}"
        if in_cart:
            label += f" ✅ ×{qty}"

        with cols[i % 5]:
            image_path = product.get("image")
            if image_path and Path(image_path).exists():
                st.image(image_path, use_container_width=True)
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
