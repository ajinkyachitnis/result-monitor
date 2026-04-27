- name: Run monitor
  env:
    TWILIO_SID: ${{ secrets.TWILIO_SID }}
    TWILIO_TOKEN: ${{ secrets.TWILIO_TOKEN }}
    TO_WHATSAPP: ${{ secrets.TO_WHATSAPP }}
  run: python monitor.pyimport os
from datetime import datetime, timezone
from twilio.rest import Client

def send_whatsapp():
    print("🔥 STARTING WHATSAPP TEST")

    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    to = os.environ.get("TO_WHATSAPP")

    print("SID present:", bool(sid))
    print("TOKEN present:", bool(token))
    print("TO:", to)

    if not sid or not token or not to:
        print("❌ Missing environment variables")
        return

    try:
        client = Client(sid, token)

        message = client.messages.create(
            body=f"✅ GitHub Actions WhatsApp Test\nTime: {datetime.now(timezone.utc)}",
            from_="whatsapp:+14155238886",
            to=to
        )
import os
from datetime import datetime, timezone
from twilio.rest import Client

def send_whatsapp():
    print("🔥 STARTING WHATSAPP TEST")

    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    to = os.environ.get("TO_WHATSAPP")

    print("SID present:", bool(sid))
    print("TOKEN present:", bool(token))
    print("TO:", to)

    if not sid or not token or not to:
        print("❌ Missing environment variables")
        return

    try:
        client = Client(sid, token)

        message = client.messages.create(
            body=f"✅ GitHub Actions WhatsApp Test\nTime: {datetime.now(timezone.utc)}",
            from_="whatsapp:+14155238886",
            to=to
        )

        print("✅ Message sent successfully")
        print("Message SID:", message.sid)

    except Exception as e:
        print("❌ Twilio error:", str(e))


def main():
    print("🚀 SCRIPT STARTED")
    send_whatsapp()


if __name__ == "__main__":
    main()
        print("✅ Message sent successfully")
        print("Message SID:", message.sid)

    except Exception as e:
        print("❌ Twilio error:", str(e))


def main():
    print("🚀 SCRIPT STARTED")
    send_whatsapp()


if __name__ == "__main__":
    main()
