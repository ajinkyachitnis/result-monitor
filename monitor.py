import requests
import json
import os
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from twilio.rest import Client

# ---------- LOGGING SETUP ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def log(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)


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
        log("State file not found. Using default.")
        return {"status": "UNKNOWN"}
    try:
        data = json.load(open(STATE_FILE))
        log(f"Loaded state: {data}")
        return data
    except Exception as e:
        log_error(f"Failed to load state: {e}")
        return {"status": "UNKNOWN"}


def save_state(state):
    try:
        json.dump(state, open(STATE_FILE, "w"))
        log(f"State saved: {state}")
    except Exception as e:
        log_error(f"Failed to save state: {e}")


# ---------- WHATSAPP ----------
def send_whatsapp(msg):
    log("Attempting to send WhatsApp message...")

    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    to = os.environ.get("TO_WHATSAPP")

    log(f"SID present: {bool(sid)}")
    log(f"TO number: {to}")

    if not sid or not token or not to:
        log_error("Missing Twilio environment variables")
        return

    try:
        client = Client(sid, token)

        message = client.messages.create(
            body=msg,
            from_="whatsapp:+14155238886",
            to=to
        )

        log(f"WhatsApp sent successfully. SID: {message.sid}")

    except Exception as e:
        log_error(f"Twilio error: {e}")


# ---------- MESSAGE FORMAT ----------
def format_up_message(data, url):
    return f"""🎉 RESULT AVAILABLE

Seat: {SEAT_NO}
Source: {url}

Response:
{json.dumps(data, indent=2)[:1200]}
"""


def format_down_message():
    return f"""⏳ RESULT NOT AVAILABLE

Seat: {SEAT_NO}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Status: Still waiting...
"""


# ---------- API HIT ----------
def hit_endpoint(i):
    url = f"https://hscresult-{i}.mahahsscboard.in/api/result/getResult/{SEAT_NO}"
    log(f"[{i}] Hitting endpoint: {url}")

    try:
        r = requests.post(url, json=PAYLOAD, headers=HEADERS, timeout=5)
        log(f"[{i}] Status code: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            log(f"[{i}] Response (truncated): {str(data)[:200]}")

            if data and data.get("error") != -1:
                log(f"[{i}] VALID RESULT FOUND")
                return True, data, url
        else:
            log(f"[{i}] Non-200 response")

    except Exception as e:
        log_error(f"[{i}] Request failed: {e}")

    return False, None, url


# ---------- PARALLEL CHECK ----------
def check_all_parallel():
    log("Starting parallel endpoint checks...")

    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(hit_endpoint, i) for i in range(1, 10)]

        for future in as_completed(futures):
            success, data, url = future.result()

            if success:
                log(f"SUCCESS from {url}")

                # cancel remaining
                for f in futures:
                    if not f.done():
                        f.cancel()

                return "UP", data, url

    log("No valid result found across endpoints")
    return "DOWN", None, None


# ---------- MAIN ----------
def main():
    log("========== SCRIPT START ==========")

    now = datetime.now(timezone.utc)
    log(f"Current UTC time: {now}")

    if now > END_DATE:
        log("Script expired. Exiting.")
        return

    state = load_state()
    prev = state.get("status", "UNKNOWN")

    log(f"Previous state: {prev}")

    current, data, url = check_all_parallel()

    log(f"Current state: {current}")

    # ---------- STATE CHANGE ----------
    if current != prev:
        log(f"STATE CHANGE DETECTED: {prev} → {current}")

        if current == "UP":
            msg = format_up_message(data, url)
            send_whatsapp(msg)

        elif current == "DOWN":
            msg = format_down_message()
            send_whatsapp(msg)

    else:
        log("No state change. No WhatsApp sent.")

    # ---------- SAVE STATE ----------
    save_state({
        "status": current,
        "last_run": now.isoformat()
    })

    log("========== SCRIPT END ==========")


if __name__ == "__main__":
    main()
