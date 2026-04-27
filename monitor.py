import requests
import json
import os
from datetime import datetime
from twilio.rest import Client

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


def send_whatsapp(msg):
    client = Client(
        os.environ["TWILIO_SID"],
        os.environ["TWILIO_TOKEN"]
    )
    client.messages.create(
        body=msg,
        from_="whatsapp:+14155238886",
        to=os.environ["TO_WHATSAPP"]
    )


def main():
    if is_expired():
        return

    state = load_state()
    prev = state.get("status", "UNKNOWN")

    current = check_service()

    print("Prev:", prev, "Current:", current)

    if prev in ["DOWN", "UNKNOWN"] and current == "UP":
        send_whatsapp("🎉 RESULT IS OUT!")

    save_state({
        "status": current,
        "last_run": datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    main()
