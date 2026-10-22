
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PRICE_URL = "https://www.adidas.de/en/samba-og-shoes/KJ7447.html"
MIN_PRICE = 130.0

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE = Path("price_state.json")


def send_message(text):
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    response.raise_for_status()
    if not response.json().get("ok"):
        raise RuntimeError("Telegram rejected the message")


def get_price():
    response = requests.get(
        PRICE_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-DE,en;q=0.9",
        },
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    match = re.search(
        r"\bPrice\s*€\s*(\d+(?:[.,]\d{1,2})?)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise RuntimeError("Could not find Adidas price")

    return float(match.group(1).replace(",", "."))


def main():
    if os.getenv("SEND_TEST", "false").lower() == "true":
        send_message("✅ Adidas price tracker is running!")

    previous_price = None

    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        previous_price = state.get("last_price")

    price = get_price()
    print(f"Current price: {price:.2f} EUR")
    print(f"Previous price: {previous_price}")

    if price <= MIN_PRICE and (
        previous_price is None or price < previous_price
    ):
        send_message(
            f"👟 Adidas Samba OG\n"
            f"Price: {price:.2f} €\n"
            f"Previous: {previous_price} €\n\n"
            f"{PRICE_URL}"
        )

    STATE_FILE.write_text(
        json.dumps({"last_price": price}, indent=2)
    )


if __name__ == "__main__":
    main()
