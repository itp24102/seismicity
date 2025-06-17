import os
import time
import requests
import boto3
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeopyError

# === Περιβάλλον ===
URL = "http://www.geophysics.geol.uoa.gr/stations/maps/seismicity.xml"
S3_BUCKET = os.environ.get("S3_BUCKET", "seismicity-app-bucket")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))  # default = 10s

# === Geolocator ===
geolocator = Nominatim(user_agent="seismicity-poller")

# === S3 Client (εκτός function για επαναχρησιμοποίηση) ===
s3 = boto3.client("s3", region_name=AWS_REGION)

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="el", timeout=10)
        return location.raw.get('address', {}).get('city', 'Άγνωστη') if location else "Άγνωστη"
    except (GeocoderTimedOut, GeopyError) as e:
        print(f"⚠️ Geocoding failed for ({lat}, {lon}): {e}")
        return "Άγνωστη"

def fetch_xml():
    print(f"📥 Fetching data from {URL}")
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return ET.fromstring(response.content)

def parse_and_upload(xml_root):
    for event in xml_root.findall("event"):
        data = {
            "date": event.findtext("date"),
            "time": event.findtext("time"),
            "lat": event.findtext("lat"),
            "lon": event.findtext("lon"),
            "depth": event.findtext("depth"),
            "mag": event.findtext("mag"),
        }

        if not all(data.values()):
            print("⚠️ Skipped incomplete event")
            continue

        # === Δημιουργία ISO timestamp ===
        timestamp = f"{data['date']}T{data['time']}"
        try:
            iso_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").isoformat()
        except ValueError:
            print(f"⚠️ Invalid timestamp: {timestamp}")
            continue

        # === Προσθήκη πόλης ===
        data["city"] = reverse_geocode(data["lat"], data["lon"])

        # === Ανέβασμα σε S3 ===
        s3_key = f"{S3_KEY_PREFIX}{iso_ts}.json"
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json"
            )
            print(f"✅ Uploaded: {s3_key} | Πόλη: {data['city']}")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")

def main():
    root = fetch_xml()
    parse_and_upload(root)

# === Polling Loop ===
if __name__ == "__main__":
    while True:
        try:
            print(f"\n🔁 Polling at {datetime.utcnow().isoformat()}Z")
            main()
        except Exception as e:
            print(f"❌ Σφάλμα: {e}")
        time.sleep(POLL_INTERVAL)
