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
        status = r.status_code
        logging.info(f"[{i}] Status: {status}")

        try:
            data = r.json()
        except:
            data = {"raw": r.text[:300]}

        return status, data, url

    except Exception as e:
        logging.error(f"[{i}] Exception: {e}")
        return 599, None, url  # treat as server failure


# ---------- PRIORITY CHECK ----------
def check_all_parallel():
    results = []

    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(hit_endpoint, i) for i in range(1, 10)]

        for future in as_completed(futures):
            status, data, url = future.result()
            results.append((status, data, url))

    # 🔥 PRIORITY LOGIC

    # 1️⃣ Prefer 200
    for status, data, url in results:
        if status == 200:
            logging.info(f"Selected 200 from {url}")
            return "UP", status, data, url

    # 2️⃣ Prefer 400
    for status, data, url in results:
        if status == 400:
            logging.info(f"Selected 400 from {url}")
            return "UP", status, data, url

    # 3️⃣ Any non-5xx
    for status, data, url in results:
        if status < 500:
            logging.info(f"Selected fallback {status} from {url}")
            return "UP", status, data, url

    # 4️⃣ All failed
    logging.info("All endpoints failed (5xx)")
    return "DOWN", None, None, None


# ---------- MESSAGE FORMAT ----------
def format_up_message(status, data, url):
    return f"""🟢 SERVICE UP

Status: {status}
URL: {url}
Seat: {SEAT_NO}

Response:
{json.dumps(data, indent=2)[:1200]}
"""


def format_down_message():
    return f"""🔴 SERVICE DOWN

All servers returned 5xx
Seat: {SEAT_NO}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""


# ---------- MAIN ----------
def main():
    logging.info("===== SCRIPT START =====")

    now = datetime.now(timezone.utc)

    if now > END_DATE:
        logging.info("Expired. Exiting.")
        return

    state = load_state()
    prev = state.get("status", "UNKNOWN")

    logging.info(f"Previous state: {prev}")

    current, status, data, url = check_all_parallel()

    logging.info(f"Current state: {current}")

    # 🔥 SEND ONLY ON CHANGE
    if current != prev:
        logging.info(f"State change: {prev} → {current}")

        if current == "UP":
            send_whatsapp(format_up_message(status, data, url))
        else:
            send_whatsapp(format_down_message())
    else:
        logging.info("No state change. No message sent.")

    save_state({
        "status": current,
        "last_run": now.isoformat()
    })

    logging.info("===== SCRIPT END =====")


if __name__ == "__main__":
    main()
