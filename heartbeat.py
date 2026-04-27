import json
import os
from datetime import datetime, timedelta
from twilio.rest import Client

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    return json.load(open(STATE_FILE))


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
    state = load_state()
    last_run = state.get("last_run")

    if not last_run:
        send_whatsapp("❌ Cron DOWN (never ran)")
        return

    last_run_time = datetime.fromisoformat(last_run)

    if datetime.utcnow() - last_run_time < timedelta(hours=1):
        send_whatsapp("✅ Cron is UP and running")
    else:
        send_whatsapp("🚨 Cron is DOWN")


if __name__ == "__main__":
    main()
