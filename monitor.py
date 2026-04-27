import requests
import json
import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from twilio.rest import Client

STATE_FILE = "state.json"
SEAT_NO = "T089759"

PAYLOAD = {
    "mother": "MANISHA"   # ⚠️ MUST be correct
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
    client = Client(
        os.environ["TWILIO_SID"],
        os.environ["TWILIO_TOKEN"]
    )

    message = client.messages.create(
        body=msg,
        from_="whatsapp:+14155238886",
        to=os.environ["TO_WHATSAPP"]
    )

    print("Message sent:", message.sid)


# ---------- FORMAT RESPONSE ----------
def format_full_response(data, url):
    return f"""🎉 RESULT FOUND

Source: {url}

Full Response:
{json.dumps(data, indent=2)[:1500]}
"""


# ---------- API HIT ----------
def hit_endpoint(i):
    url = f"https://hscresult-{i}.mahahsscboard.in/api/result/getResult/{SEAT_NO}"

    try:
        r = requests.post(url, json=PAYLOAD, headers=HEADERS, timeout=5)

        print(f"[{i}] Status:", r.status_code)

        if r.status_code == 200:
            data = r.json()
            print(f"[{i}] Response:", data)

            if data and data.get("error") != -1:
                return True, data, url

    except Exception as e:
        print(f"[{i}] Failed:", e)

    return False, None, url


# ---------- PARALLEL CHECK ----------
def check_all_parallel():
    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(hit_endpoint, i) for i in range(1, 10)]

        for future in as_completed(futures):
            success, data, url = future.result()

            if success:
                print("SUCCESS:", url)

                # cancel remaining
                for f in futures:
                    if not f.done():
                        f.cancel()

                return "UP", data, url

    return "DOWN", None, None


# ---------- MAIN ----------
def main():
    if datetime.now(timezone.utc) > END_DATE:
        return

    state = load_state()
    prev = state.get("status", "UNKNOWN")

    current, data, url = check_all_parallel()

    print("Prev:", prev, "| Current:", current)

    # ✅ Trigger only once
    if true:
        message = format_full_response(data, url)
        send_whatsapp(message)

    save_state({
        "status": current,
        "last_run": datetime.now(timezone.utc).isoformat()
    })


if __name__ == "__main__":
    main()
