import os
import requests
import json
import boto3
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")  # Ενημερώθηκε σε eu-west-1

s3_client = boto3.client("s3", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
geolocator = Nominatim(user_agent="seismicity-lambda")

def reverse_geocode(lat, lon):
    try:
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            print(f"⚠️ Μη έγκυρες συντεταγμένες: lat={lat}, lon={lon}")
            return "Μη έγκυρες συντεταγμένες"
        location = geolocator.reverse((lat, lon), language="el", exactly_one=True, timeout=10)
        return location.address if location else "Άγνωστη τοποθεσία"
    except GeocoderTimedOut:
        print("⚠️ Timeout κατά την αντίστροφη γεωκωδικοποίηση")
        return "Timeout"
    except Exception as e:
        print(f"⚠️ Σφάλμα γεωκωδικοποίησης: {e}")
        return "Σφάλμα γεωκωδικοποίησης"

def fetch_events_from_seismicportal(limit=200):
    start = (datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z"
    url = (
        "https://www.seismicportal.eu/fdsnws/event/1/query"
        f"?format=json&starttime={start}&limit={limit}"
        "&orderby=time-asc&minlat=34&maxlat=42&minlon=19&maxlon=30"
    )
    print(f"🔗 Querying SeismicPortal: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        events = []
        for feature in data.get("features", []):
            try:
                event_id = feature["id"]
                props = feature["properties"]
                coords = feature["geometry"].get("coordinates")

                if not coords or len(coords) < 3:
                    print(f"⚠️ Μη έγκυρες συντεταγμένες για event {event_id}: {coords}")
                    continue

                lon, lat, depth = coords
                if not all(isinstance(x, (int, float)) for x in [lat, lon, depth]):
                    print(f"⚠️ Μη έγκυρες τιμές συντεταγμένων για event {event_id}: lat={lat}, lon={lon}, depth={depth}")
                    continue

                timestamp = props.get("time")
                magnitude = props.get("mag")
                if timestamp is None or magnitude is None:
                    print(f"⚠️ Ελλιπή δεδομένα για event {event_id}: timestamp={timestamp}, magnitude={magnitude}")
                    continue

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
                print(f"⚠️ Παράβλεψη event {event_id} λόγω σφάλματος: {e}")
        return events
    except requests.exceptions.RequestException as e:
        print(f"❌ Σφάλμα κατά την κλήση του SeismicPortal: {e}")
        return []

def parse_and_upload(events):
    if not S3_BUCKET:
        print("❌ Η μεταβλητή S3_BUCKET δεν έχει οριστεί!")
        return []

    if not events:
        print("Δεν βρέθηκαν νέα συμβάντα.")
        return []

    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"{S3_KEY_PREFIX}{today}.json"
    print(f"📦 S3 Bucket: {S3_BUCKET}, Key: {key}")

    try:
        old_data = s3_client.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read().decode("utf-8")
        existing = json.loads(old_data)
    except s3_client.exceptions.NoSuchKey:
        existing = []
    except Exception as e:
        print(f"❌ Σφάλμα κατά την ανάγνωση από S3: {e}")
        existing = []

    existing_ids = {e["id"] for e in existing}
    new_events = [e for e in events if e["id"] not in existing_ids]

    if not new_events:
        print("⏭️ Δεν υπάρχουν νέα δεδομένα για αποθήκευση.")
        return []

    combined = existing + new_events
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(combined, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json"
        )
        print(f"✅ Αποθηκεύτηκαν {len(new_events)} νέα συμβάντα στο {key}.")
    except Exception as e:
        print(f"❌ Σφάλμα κατά την εγγραφή στο S3: {e}")
    return new_events

def handler(event, context):
    print(f"🌍 Polling από SeismicPortal: {datetime.utcnow().isoformat()}Z")
    try:
        events = fetch_events_from_seismicportal()
        new_events = parse_and_upload(events)

        if new_events:
            print(f"🚀 Προώθηση {len(new_events)} νέων σεισμικών δεδομένων στο influx-writer")
            try:
                lambda_client.invoke(
                    FunctionName="influx-writer",
                    InvocationType="Event",
                    Payload=json.dumps({"events": new_events}, ensure_ascii=False).encode("utf-8")
                )
            except Exception as e:
                print(f"❌ Σφάλμα κατά την κλήση του influx-writer: {e}")
                raise e
        else:
            print("ℹ️ Δεν υπάρχουν νέα δεδομένα προς αποστολή στο influx-writer.")
    except Exception as e:
        print(f"❌ Σφάλμα: {e}")
        raise e

    return {"statusCode": 200, "body": "Poll from SeismicPortal completed."}