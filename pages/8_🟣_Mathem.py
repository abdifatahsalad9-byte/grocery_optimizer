import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(page_title="Mathem", page_icon="🟣", layout="wide")

st.title("🟣 Mathem — Importera produkter")
st.warning("**Mathem blockerar automatisk sökning.** Det går inte att hämta produkter från Mathem automatiskt just nu.")

st.markdown("""
### Så kan du ändå lägga till Mathem-produkter:

1. Gå till **[mathem.se](https://www.mathem.se)** i din webbläsare
2. Sök efter produkten du vill lägga till
3. Gå sedan till **➕ Hantera varor** i den här appen och lägg till produkten manuellt

Vi jobbar på att lösa detta — Mathem kräver en mer avancerad lösning.
""")
