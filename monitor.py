import requests
import json
import os
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from twilio.rest import Client

# ---------- LOGGING ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ---------- CONFIG ----------
SEAT_NO = "T089759"

PAYLOAD = {
    "mother": "MANISHA"
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://hscresult.mahahsscboard.in",
    "Referer": "https://hscresult.mahahsscboard.in/"
}


# ---------- WHATSAPP ----------
def send_whatsapp(msg):
    try:
        client = Client(
            os.environ["TWILIO_SID"],
            os.environ["TWILIO_TOKEN"]
        )

        message = client.messages.create(
            body=msg,
            from_="whatsapp:+14155238886",
            to=os.environ["TO_WHATSAPP"]
        )

        logging.info(f"WhatsApp sent: {message.sid}")

    except Exception as e:
        logging.error(f"Twilio error: {e}")


# ---------- API HIT ----------
def hit_endpoint(i):
    url = f"https://hscresult-{i}.mahahsscboard.in/api/result/getResult/{SEAT_NO}"
    logging.info(f"[{i}] Calling {url}")

    try:
        r = requests.post(url, json=PAYLOAD, headers=HEADERS, timeout=5)
        logging.info(f"[{i}] Status: {r.status_code}")

        if r.status_code != 503:
            try:
                data = r.json()
            except:
                data = {"raw": r.text[:300]}

            return "UP", data, url
        else:
            return "DOWN", None, url

    except Exception as e:
        logging.error(f"[{i}] Exception: {e}")
        return "DOWN", None, url


# ---------- PARALLEL CHECK ----------
def check_all_parallel():
    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(hit_endpoint, i) for i in range(1, 10)]

        for future in as_completed(futures):
            status, data, url = future.result()

            if status == "UP":
                # cancel remaining
                for f in futures:
                    if not f.done():
                        f.cancel()

                return "UP", data, url

    return "DOWN", None, None


# ---------- MESSAGE FORMAT ----------
def format_up_message(data, url):
    return f"""🟢 SERVICE UP

URL: {url}
Seat: {SEAT_NO}

Response:
{json.dumps(data, indent=2)[:1000]}
"""


def format_down_message():
    return f"""🔴 SERVICE DOWN (503)

Seat: {SEAT_NO}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""


# ---------- MAIN ----------
def main():
    logging.info("===== SCRIPT START =====")

    current, data, url = check_all_parallel()

    logging.info(f"Current state: {current}")

    # 🔥 ALWAYS SEND (no state check)
    if current == "UP":
        send_whatsapp(format_up_message(data, url))
    else:
        send_whatsapp(format_down_message())

    logging.info("===== SCRIPT END =====")


if __name__ == "__main__":
    main()
