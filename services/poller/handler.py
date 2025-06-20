# handler.py
import os
import requests
import json
import boto3
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

s3_client = boto3.client("s3", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
geolocator = Nominatim(user_agent="seismicity-lambda")

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), language="el", exactly_one=True, timeout=10)
        return location.address if location else "Άγνωστη τοποθεσία"
    except GeocoderTimedOut:
        return "Timeout"
    except Exception as e:
        print(f"⚠️ Reverse geocode error: {e}")
        return "Σφάλμα"

def fetch_events_from_seismicportal(limit=20):
    url = f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json&limit={limit}&orderby=time-asc&minlat=34&maxlat=42&minlon=19&maxlon=30"
    print(f"🔗 Querying SeismicPortal: {url}")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    events = []
    for feature in data.get("features", []):
        try:
            event_id = feature["id"]
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]

            timestamp = props.get("time")
            if not timestamp:
                print(f"⚠️ Missing timestamp in event: {event_id}")
                continue

            magnitude = props.get("mag", 0.0)
            depth = coords[2] if len(coords) > 2 else 0.0
            lon = coords[0] if len(coords) > 0 else 0.0
            lat = coords[1] if len(coords) > 1 else 0.0
            location = reverse_geocode(lat, lon)

            events.append({
                "id": event_id,
                "timestamp": timestamp,
                "magnitude": magnitude,
                "lat": lat,
                "lon": lon,
                "depth": depth,
                "location": location
            })
        except Exception as e:
            print(f"⚠️ Παράβλεψη event: {e}")
            print(json.dumps(feature, ensure_ascii=False, indent=2))

    return events

def parse_and_upload(events):
    if not events:
        print("⚠️ Δεν βρέθηκαν νέα συμβάντα.")
        return []

    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"{S3_KEY_PREFIX}{today}.json"

    try:
        old_data = s3_client.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read().decode("utf-8")
        existing = json.loads(old_data)
    except s3_client.exceptions.NoSuchKey:
        existing = []

    existing_ids = {e["id"] for e in existing}
    new_events = [e for e in events if e["id"] not in existing_ids]

    if not new_events:
        print("⏭️ Δεν υπάρχουν νέα δεδομένα για αποθήκευση.")
        return []

    combined = existing + new_events
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(combined, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json"
    )
    print(f"✅ Αποθηκεύτηκαν {len(new_events)} νέα συμβάντα στο {key}.")
    return new_events

def handler(event, context):
    print(f"🌍 Polling από SeismicPortal: {datetime.utcnow().isoformat()}Z")
    try:
        events = fetch_events_from_seismicportal()
        new_events = parse_and_upload(events)

        if new_events:
            print("📤 Στέλνονται δεδομένα στο influx-writer...")
            lambda_client.invoke(
                FunctionName="influx-writer",
                InvocationType="Event",
                Payload=json.dumps({"events": new_events}).encode("utf-8")
            )
    except Exception as e:
        print(f"❌ Σφάλμα: {e}")
    return {"statusCode": 200, "body": "Poll from SeismicPortal completed."}
