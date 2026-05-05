import json
import time
import requests
from pathlib import Path

import streamlit as st

PRODUCTS_FILE = Path("data/products.json")
IMAGES_DIR    = Path("static/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.willys.se/",
}

UNITS    = ["förp", "kg", "st", "L"]
EMOJIS   = ["🍗","🥩","🐟","🌭","🥛","🧈","🥚","🧀","🍶","🥑","🍌","🍋","🍅",
             "🥒","🫑","🥬","🥔","🧅","🧄","🌽","🥝","🥭","👶","🍼","🥣","🍝",
             "🍚","🌾","🫙","🥫","🍯","🧃","🍞","🫓","🧴","🧻","🧽","🪒","🪥",
             "🗑️","🛍️","🍦","🍟","🍫","🌮","🟡","🟥","🌶️","🍊","🍏"]


def load_products() -> dict:
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_products(data: dict):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_willys(query: str) -> list[dict]:
    url = f"https://www.willys.se/search?q={requests.utils.quote(query)}&searchType=PRODUCT"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []


def download_image(url: str, path: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        path.write_bytes(r.content)
        return True
    except Exception:
        return False


def make_id(name: str) -> str:
    replacements = {"å":"a","ä":"a","ö":"o","é":"e"," ":"_","/":"_","-":"_","&":""}
    result = name.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return "".join(c for c in result if c.isalnum() or c == "_").strip("_")


# ── Layout ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hantera varor", page_icon="➕", layout="wide")
st.title("➕ Hantera varor")

products_data = load_products()
categories    = list(products_data["categories"].keys())

tab1, tab2, tab3 = st.tabs(["Lägg till vara", "Ändra bild", "Ta bort vara"])

# ── Tab 1: Lägg till vara ──────────────────────────────────────────────────────
with tab1:
    st.subheader("Lägg till ny vara")

    col1, col2 = st.columns(2)

    with col1:
        name     = st.text_input("Varunamn *", placeholder="t.ex. Havregryn 500g")
        category = st.selectbox("Kategori *", categories + ["➕ Ny kategori"])
        if category == "➕ Ny kategori":
            category = st.text_input("Namn på ny kategori")
        unit  = st.selectbox("Enhet", UNITS)
        emoji = st.selectbox("Emoji", EMOJIS)

    with col2:
        st.markdown("**Förhandsgranska bild från Willys**")
        query = st.text_input("Sökord (lämna tomt för att använda varunamnet)", placeholder="t.ex. havregryn 500g")

        if name:
            search_query = query if query else name
            if st.button("🔍 Sök bild", use_container_width=True):
                with st.spinner("Söker på Willys..."):
                    results = search_willys(search_query)
                st.session_state.search_results = results
                st.session_state.selected_idx   = 0

        if "search_results" in st.session_state and st.session_state.search_results:
            results = st.session_state.search_results
            options = [f"{i+1}. {r.get('name','?')}" for i, r in enumerate(results[:6])]
            chosen  = st.radio("Välj rätt produkt:", options, index=st.session_state.selected_idx)
            st.session_state.selected_idx = options.index(chosen)

            selected = results[st.session_state.selected_idx]
            img_url  = selected.get("image", {}).get("url")
            if img_url:
                st.image(img_url, width=150)
                st.caption(selected.get("name"))

    st.divider()

    if st.button("✅ Lägg till vara", type="primary", use_container_width=True):
        if not name or not category:
            st.error("Fyll i varunamn och kategori.")
        else:
            pid = make_id(name)

            # Kolla om id redan finns
            all_ids = [p["id"] for prods in products_data["categories"].values() for p in prods]
            if pid in all_ids:
                st.error(f"En vara med id '{pid}' finns redan.")
            else:
                # Ladda ner bild
                image_path = None
                if "search_results" in st.session_state and st.session_state.search_results:
                    selected = st.session_state.search_results[st.session_state.get("selected_idx", 0)]
                    img_url  = selected.get("image", {}).get("url")
                    if img_url:
                        dest = IMAGES_DIR / f"{pid}.jpg"
                        if download_image(img_url, dest):
                            image_path = str(dest)

                # Bygg produkt
                new_product = {"id": pid, "name": name, "emoji": emoji, "unit": unit}
                if image_path:
                    new_product["image"] = image_path

                # Lägg till i rätt kategori
                if category not in products_data["categories"]:
                    products_data["categories"][category] = []
                products_data["categories"][category].append(new_product)
                save_products(products_data)

                st.success(f"✅ '{name}' är tillagd under {category}!")
                if image_path:
                    st.image(image_path, width=150)
                else:
                    st.info("Ingen bild hittades — emoji används istället.")

                # Rensa sökresultat
                st.session_state.pop("search_results", None)
                time.sleep(1)
                st.rerun()

# ── Tab 2: Ändra bild ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("Ändra bild på en vara")

    all_products = [
        p for prods in products_data["categories"].values() for p in prods
    ]
    product_names = [f"{p['emoji']} {p['name']}" for p in all_products]
    chosen_name   = st.selectbox("Välj vara", product_names)
    chosen        = all_products[product_names.index(chosen_name)]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Nuvarande bild**")
        img = chosen.get("image")
        if img and Path(img).exists():
            st.image(img, width=150)
        else:
            st.write(chosen["emoji"])

    with col2:
        st.markdown("**Ny bild**")
        fix_query = st.text_input("Sökord", value=chosen["name"], key="fix_query")
        if st.button("🔍 Sök", key="fix_search"):
            with st.spinner("Söker..."):
                results = search_willys(fix_query)
            st.session_state.fix_results = results
            st.session_state.fix_idx     = 0

        if "fix_results" in st.session_state and st.session_state.fix_results:
            results  = st.session_state.fix_results
            options  = [f"{i+1}. {r.get('name','?')}" for i, r in enumerate(results[:6])]
            chosen_r = st.radio("Välj:", options, index=st.session_state.fix_idx, key="fix_radio")
            st.session_state.fix_idx = options.index(chosen_r)

            selected = results[st.session_state.fix_idx]
            img_url  = selected.get("image", {}).get("url")
            if img_url:
                st.image(img_url, width=150)

            if st.button("💾 Spara ny bild", type="primary"):
                dest = IMAGES_DIR / f"{chosen['id']}.jpg"
                if download_image(img_url, dest):
                    # Uppdatera products.json
                    for prods in products_data["categories"].values():
                        for p in prods:
                            if p["id"] == chosen["id"]:
                                p["image"] = str(dest)
                    save_products(products_data)
                    st.success("✅ Bild sparad!")
                    st.session_state.pop("fix_results", None)
                    time.sleep(1)
                    st.rerun()

# ── Tab 3: Ta bort vara ────────────────────────────────────────────────────────
with tab3:
    st.subheader("Ta bort vara")

    del_category = st.selectbox("Kategori", categories, key="del_cat")
    cat_products = products_data["categories"].get(del_category, [])

    if cat_products:
        del_names  = [f"{p['emoji']} {p['name']}" for p in cat_products]
        del_chosen = st.selectbox("Vara att ta bort", del_names)
        del_prod   = cat_products[del_names.index(del_chosen)]

        img = del_prod.get("image")
        if img and Path(img).exists():
            st.image(img, width=100)

        if st.button("🗑️ Ta bort", type="primary"):
            products_data["categories"][del_category] = [
                p for p in cat_products if p["id"] != del_prod["id"]
            ]
            save_products(products_data)
            st.success(f"✅ '{del_prod['name']}' är borttagen.")
            time.sleep(1)
            st.rerun()
    else:
        st.info("Inga varor i den här kategorin.")
