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

UNITS  = ["förp", "kg", "st", "L"]
EMOJIS = ["🍗","🥩","🐟","🌭","🥛","🧈","🥚","🧀","🍶","🥑","🍌","🍋","🍅",
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


def show_image_picker(results: list[dict], key: str) -> dict | None:
    """Visar bilder som klickbara knappar. Returnerar vald produkt."""
    if not results:
        return None

    selected_key = f"{key}_selected"
    if selected_key not in st.session_state:
        st.session_state[selected_key] = 0

    st.markdown("**Välj rätt bild:**")
    cols = st.columns(min(len(results[:6]), 6))

    for i, product in enumerate(results[:6]):
        img_url = product.get("image", {}).get("url")
        with cols[i]:
            if img_url:
                st.image(img_url, use_container_width=True)
            label = "✅ Vald" if st.session_state[selected_key] == i else f"Välj {i+1}"
            if st.button(label, key=f"{key}_btn_{i}", use_container_width=True):
                st.session_state[selected_key] = i
                st.rerun()
            st.caption(product.get("name","")[:25])

    return results[st.session_state[selected_key]]


# ── Layout ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hantera varor", page_icon="➕", layout="wide")
st.title("➕ Hantera varor")

products_data = load_products()
categories    = list(products_data["categories"].keys())

tab1, tab2, tab3, tab4 = st.tabs(["Lägg till vara", "Ändra bild", "Ta bort vara", "Sortera varor"])

# ── Tab 1: Lägg till vara ──────────────────────────────────────────────────────
with tab1:
    st.subheader("Lägg till ny vara")

    col1, col2 = st.columns([1, 2])
    with col1:
        name     = st.text_input("Varunamn *", placeholder="t.ex. Havregryn 500g")
        category = st.selectbox("Kategori *", categories + ["➕ Ny kategori"])
        if category == "➕ Ny kategori":
            category = st.text_input("Namn på ny kategori")
        unit  = st.selectbox("Enhet", UNITS)
        emoji = st.selectbox("Emoji", EMOJIS)
        query = st.text_input("Sökord på Willys", placeholder="lämna tomt = använd varunamnet")

        if st.button("🔍 Sök bild på Willys", use_container_width=True, disabled=not name):
            with st.spinner("Söker..."):
                results = search_willys(query if query else name)
            st.session_state.add_results = results
            st.session_state.pop("add_selected", None)

    with col2:
        if "add_results" in st.session_state:
            selected = show_image_picker(st.session_state.add_results, "add")

            st.divider()
            if st.button("✅ Lägg till vara", type="primary", use_container_width=True):
                if not name or not category:
                    st.error("Fyll i varunamn och kategori.")
                else:
                    pid     = make_id(name)
                    all_ids = [p["id"] for prods in products_data["categories"].values() for p in prods]

                    if pid in all_ids:
                        st.error(f"'{name}' finns redan.")
                    else:
                        image_path = None
                        if selected:
                            img_url = selected.get("image", {}).get("url")
                            if img_url:
                                dest = IMAGES_DIR / f"{pid}.jpg"
                                if download_image(img_url, dest):
                                    image_path = str(dest)

                        new_product = {"id": pid, "name": name, "emoji": emoji, "unit": unit}
                        if image_path:
                            new_product["image"] = image_path

                        if category not in products_data["categories"]:
                            products_data["categories"][category] = []
                        products_data["categories"][category].append(new_product)
                        save_products(products_data)

                        st.success(f"✅ '{name}' tillagd!")
                        st.session_state.pop("add_results", None)
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("Skriv ett varunamn och tryck 'Sök bild' för att komma igång.")

# ── Tab 2: Ändra bild ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("Ändra bild på en vara")

    all_products  = [p for prods in products_data["categories"].values() for p in prods]
    product_names = [f"{p['emoji']} {p['name']}" for p in all_products]
    chosen_name   = st.selectbox("Välj vara", product_names)
    chosen        = all_products[product_names.index(chosen_name)]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Nuvarande bild**")
        img = chosen.get("image")
        if img and Path(img).exists():
            st.image(img, width=150)
        else:
            st.write(chosen["emoji"])

        fix_query = st.text_input("Sökord", value=chosen["name"])
        if st.button("🔍 Sök ny bild", use_container_width=True):
            with st.spinner("Söker..."):
                results = search_willys(fix_query)
            st.session_state.fix_results = results
            st.session_state.pop("fix_selected", None)

    with col2:
        if "fix_results" in st.session_state:
            selected = show_image_picker(st.session_state.fix_results, "fix")

            st.divider()
            if st.button("💾 Spara ny bild", type="primary", use_container_width=True):
                img_url = selected.get("image", {}).get("url") if selected else None
                if img_url:
                    dest = IMAGES_DIR / f"{chosen['id']}.jpg"
                    if download_image(img_url, dest):
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

    del_category = st.selectbox("Kategori", categories)
    cat_products = products_data["categories"].get(del_category, [])

    if cat_products:
        del_names  = [f"{p['emoji']} {p['name']}" for p in cat_products]
        del_chosen = st.selectbox("Välj vara", del_names)
        del_prod   = cat_products[del_names.index(del_chosen)]

        img = del_prod.get("image")
        if img and Path(img).exists():
            st.image(img, width=120)

        st.warning(f"Är du säker på att du vill ta bort **{del_prod['name']}**?")
        if st.button("🗑️ Ja, ta bort", type="primary"):
            products_data["categories"][del_category] = [
                p for p in cat_products if p["id"] != del_prod["id"]
            ]
            save_products(products_data)
            st.success(f"✅ '{del_prod['name']}' är borttagen.")
            time.sleep(1)
            st.rerun()
    else:
        st.info("Inga varor i den här kategorin.")

# ── Tab 4: Sortera varor ───────────────────────────────────────────────────────
with tab4:
    st.subheader("Sortera varor")
    st.caption("Flytta varor upp/ner inom en kategori, eller flytta till en annan kategori.")

    sort_category = st.selectbox("Välj kategori", categories, key="sort_cat")
    cat_products  = products_data["categories"].get(sort_category, [])

    if not cat_products:
        st.info("Inga varor i den här kategorin.")
    else:
        for i, product in enumerate(cat_products):
            img   = product.get("image")
            col_img, col_name, col_up, col_down, col_move = st.columns([0.8, 4, 0.7, 0.7, 2])

            with col_img:
                if img and Path(img).exists():
                    st.image(img, use_container_width=True)
                else:
                    st.markdown(f"<div style='font-size:1.6rem;text-align:center'>{product['emoji']}</div>", unsafe_allow_html=True)

            with col_name:
                st.markdown(f"<div style='padding-top:10px;font-weight:500'>{product['name']}</div>", unsafe_allow_html=True)

            with col_up:
                if i > 0 and st.button("↑", key=f"up_{product['id']}"):
                    lst = products_data["categories"][sort_category]
                    lst[i], lst[i - 1] = lst[i - 1], lst[i]
                    save_products(products_data)
                    st.rerun()

            with col_down:
                if i < len(cat_products) - 1 and st.button("↓", key=f"down_{product['id']}"):
                    lst = products_data["categories"][sort_category]
                    lst[i], lst[i + 1] = lst[i + 1], lst[i]
                    save_products(products_data)
                    st.rerun()

            with col_move:
                other_cats = [c for c in categories if c != sort_category]
                new_cat = st.selectbox(
                    "Flytta till",
                    ["— välj —"] + other_cats,
                    key=f"move_{product['id']}",
                    label_visibility="collapsed",
                )
                if new_cat != "— välj —":
                    products_data["categories"][sort_category].remove(product)
                    products_data["categories"][new_cat].append(product)
                    save_products(products_data)
                    st.success(f"✅ Flyttad till {new_cat}!")
                    time.sleep(0.5)
                    st.rerun()

            st.divider()
