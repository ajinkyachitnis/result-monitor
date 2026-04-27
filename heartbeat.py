import json
import os
from datetime import datetime, timedelta, timezone
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

    message = client.messages.create(
        body=msg,
        from_="whatsapp:+14155238886",
        to=os.environ["TO_WHATSAPP"]
    )

    print("Message sent:", message.sid)


def main():
    now = datetime.now(timezone.utc)

    print("Current UTC:", now)

    # 🔥 Run only every 6 hours
    if now.hour % 6 != 0:
        print("Skipping heartbeat (not 6-hour interval)")
        return

    state = load_state()
    last_run = state.get("last_run")

    print("State:", state)

    if not last_run:
        send_whatsapp("❌ Cron DOWN (never ran)")
        return

    last_run_time = datetime.fromisoformat(last_run)

    # Check if monitor ran within last 1 hour
    if now - last_run_time < timedelta(hours=1):
        send_whatsapp(
            f"✅ Cron UP\nLast run: {last_run_time}\nNow: {now}"
        )
    else:
        send_whatsapp(
            f"🚨 Cron DOWN\nLast run: {last_run_time}\nNow: {now}"
        )


if __name__ == "__main__":
    main()
