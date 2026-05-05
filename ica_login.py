"""
Kör detta skript EN GÅNG för att logga in på ICA.
Sessionen sparas och används sedan automatiskt av appen.

Användning:
    python3 ica_login.py
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path("data/ica_session.json")


def main():
    print("=" * 50)
    print("ICA-inloggning")
    print("=" * 50)
    print()
    print("Ett webbläsarfönster öppnas nu.")
    print("1. Logga in på ICA med ditt konto")
    print("2. Välj din ICA-butik")
    print("3. Gå till sökfältet och sök på valfri vara")
    print("4. Stäng INTE fönstret — tryck Enter här när klart")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="sv-SE",
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        page.goto("https://handla.ica.se/", timeout=30000)

        input("Logga in och välj butik i webbläsaren, tryck sedan Enter här... ")

        # Spara session
        storage = ctx.storage_state()
        SESSION_FILE.parent.mkdir(exist_ok=True)
        SESSION_FILE.write_text(json.dumps(storage, ensure_ascii=False, indent=2))

        # Spara också butiks-URL
        current_url = page.url
        store_url = current_url

        browser.close()

    print()
    print(f"✅ Session sparad i {SESSION_FILE}")
    print(f"   URL: {store_url}")
    print()
    print("Nu kan appen hämta riktiga ICA-priser automatiskt!")


if __name__ == "__main__":
    main()
