import os
import json
import requests

INFLUX_URL = os.environ.get("INFLUX_URL")  # π.χ. http://<ip>:8086/api/v2/write?bucket=<bucket>&org=<org>&precision=s
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")  # το token που πήραμε από το InfluxDB UI

def format_line_protocol(event):
    try:
        return (
            f"earthquake,id={event['id']},location=\"{event['location'].replace(' ', '\\ ')}\" "
            f"magnitude={event['magnitude']},depth={event['depth']},lat={event['lat']},lon={event['lon']} "
            f"{int(parse_iso8601(event['timestamp']))}"
        )
    except Exception as e:
        print(f"⚠️ Σφάλμα format για event {event}: {e}")
        return None

def parse_iso8601(timestamp_str):
    from datetime import datetime
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return int(dt.timestamp())

def handler(event, context):
    print("📡 Influx Writer ενεργοποιήθηκε")

    try:
        events = event.get("events", [])
        if not events:
            print("⚠️ Δεν δόθηκαν δεδομένα για εγγραφή.")
            return {"statusCode": 400, "body": "No events provided"}

        payload = ""
        for ev in events:
            line = format_line_protocol(ev)
            if line:
                payload += line + "\n"

        if not payload.strip():
            print("⚠️ Κανένα έγκυρο event για αποστολή.")
            return {"statusCode": 400, "body": "No valid line protocol entries"}

        headers = {
            "Authorization": f"Token {INFLUX_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8"
        }

        print(f"📨 Στέλνονται {len(events)} σεισμικά γεγονότα στο InfluxDB...")
        response = requests.post(INFLUX_URL, data=payload.encode("utf-8"), headers=headers, timeout=10)

        if response.status_code != 204:
            print(f"❌ Σφάλμα InfluxDB: HTTP {response.status_code} - {response.text}")
            return {"statusCode": response.status_code, "body": response.text}

        print(f"✅ Καταχωρήθηκαν {len(events)} σημεία στο InfluxDB.")
        return {"statusCode": 200, "body": f"Inserted {len(events)} events"}
    
    except Exception as e:
        print(f"❌ Σφάλμα στο influx-writer: {e}")
        return {"statusCode": 500, "body": str(e)}
