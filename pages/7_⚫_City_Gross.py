import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(page_title="City Gross", page_icon="⚫", layout="wide")

st.title("⚫ City Gross — Importera produkter")
st.warning("**City Gross blockerar automatisk sökning.** Det går inte att hämta produkter från City Gross automatiskt just nu.")

st.markdown("""
### Så kan du ändå lägga till City Gross-produkter:

1. Gå till **[citygross.se](https://www.citygross.se)** i din webbläsare
2. Sök efter produkten du vill lägga till
3. Gå sedan till **➕ Hantera varor** i den här appen och lägg till produkten manuellt

Vi jobbar på att lösa detta — City Gross kräver en mer avancerad lösning.
""")
