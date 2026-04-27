import requests
import json
import os
from datetime import datetime

STATE_FILE = "state.json"

URL = "https://hscresult-8.mahahsscboard.in/api/result/getResult/T089759"

PAYLOAD = {
    "mother": "MANISHA"
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://hscresult.mahahsscboard.in",
    "Referer": "https://hscresult.mahahsscboard.in/"
}

POST_URL = "https://your-api.com/notify"

END_DATE = datetime(2026, 5, 27)


def is_expired():
    return datetime.utcnow() > END_DATE


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"status": "UNKNOWN"}
    return json.load(open(STATE_FILE))


def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))


def check_service():
    try:
        r = requests.post(URL, json=PAYLOAD, headers=HEADERS, timeout=10)
        data = r.json()

        print("Response:", data)

        if data and data.get("error") != -1:
            return "UP"

        return "DOWN"

    except Exception as e:
        print("Error:", e)
        return "DOWN"


def trigger_post():
    payload = {
        "event": "RESULT_AVAILABLE",
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        r = requests.post(POST_URL, json=payload, timeout=5)
        print("Triggered POST:", r.status_code)
    except Exception as e:
        print("POST failed:", e)


def main():
    if is_expired():
        print("Expired")
        return

    prev = load_state()["status"]
    current = check_service()

    print("Prev:", prev, "Current:", current)

    if prev in ["DOWN", "UNKNOWN"] and current == "UP":
        trigger_post()

    save_state({"status": current})


if __name__ == "__main__":
    main()
