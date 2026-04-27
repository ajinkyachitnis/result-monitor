import json
import os
from datetime import datetime, timedelta, timezone
from twilio.rest import Client

STATE_FILE = "state.json"


# ---------- STATE ----------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    return json.load(open(STATE_FILE))


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


# ---------- MAIN ----------
def main():
    state = load_state()
    last_run = state.get("last_run")

    print("Loaded state:", state)

    if not last_run:
        send_whatsapp("❌ Cron DOWN (never ran)")
        return

    # ✅ Convert to timezone-aware datetime
    last_run_time = datetime.fromisoformat(last_run)

    # ✅ Use timezone-aware current time
    now = datetime.now(timezone.utc)

    print("Last run:", last_run_time)
    print("Now:", now)

    if now - last_run_time < timedelta(hours=1):
        send_whatsapp("✅ Cron is UP and running")
    else:
        send_whatsapp("🚨 Cron is DOWN")


if __name__ == "__main__":
    main()
