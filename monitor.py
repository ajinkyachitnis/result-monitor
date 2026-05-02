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
STATE_FILE = "state.json"
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

END_DATE = datetime(2026, 5, 27, tzinfo=timezone.utc)


# ---------- STATE ----------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"status": "UNKNOWN"}
    return json.load(open(STATE_FILE))


def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))


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

        # 🔥 CORE LOGIC
        if r.status_code != 503:
            try:
                data = r.json()
            except:
                data = {"raw": r.text[:300]}

            logging.info(f"[{i}] UP (non-503)")
            return "UP", data, url

        else:
            logging.info(f"[{i}] DOWN (503)")
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
{json.dumps(data, indent=2)[:1200]}
"""


def format_down_message():
    return f"""🔴 SERVICE DOWN (503)

Seat: {SEAT_NO}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""


# ---------- MAIN ----------
def main():
    send_whatsapp("✅ TEST: WhatsApp from GitHub Actions is working")
   
    logging.info("===== SCRIPT END =====")


if __name__ == "__main__":
    main()
