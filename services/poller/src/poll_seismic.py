import os
import time
import requests
import boto3
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeopyError
import xml.etree.ElementTree as ET

# === Περιβάλλον ===
URL = "http://www.geophysics.geol.uoa.gr/stations/maps/seismicity.xml"
S3_BUCKET = os.environ.get("S3_BUCKET", "seismicity-app-bucket")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

# === Geolocator ===
geolocator = Nominatim(user_agent="seismicity-poller")

# === S3 Client ===
s3 = boto3.client("s3", region_name=AWS_REGION)

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="el", timeout=10)
        return location.raw.get('address', {}).get('city', 'Άγνωστη') if location else "Άγνωστη"
    except (GeocoderTimedOut, GeopyError) as e:
        print(f"⚠️ Geocoding failed for ({lat}, {lon}): {e}")
        return "Άγνωστη"

def parse_description(desc):
    try:
        parts = desc.split("<br>")
        location = parts[0].strip()
        date_str = parts[1].split(":")[1].strip().split()[0]
        time_str = parts[1].split(":")[2].strip().split()[0]
        lat = parts[2].split(":")[1].strip().replace("N", "")
        lon = parts[3].split(":")[1].strip().replace("E", "")
        depth = parts[4].split(":")[1].strip().replace("km", "")
        mag = parts[5].split(":")[1].strip().replace("M", "").strip()

        return {
            "location": location,
            "date": f"2025-{date_str}",
            "time": time_str,
            "lat": lat,
            "lon": lon,
            "depth": depth,
            "mag": mag
        }
    except Exception as e:
        print(f"❌ Failed to parse description: {desc} — {e}")
        return None

def fetch_xml():
    print(f"📥 Fetching data from {URL}")
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return ET.fromstring(response.content)

def parse_and_upload(xml_root):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    s3_key = f"{S3_KEY_PREFIX}{today}.json"
    local_tmp_file = f"/tmp/events_{today}.json"
    daily_events = []

    # Αν υπάρχει τοπικό αρχείο (σε pod), το φορτώνουμε για να αποφύγουμε διπλοεγγραφές
    if os.path.exists(local_tmp_file):
        with open(local_tmp_file, "r", encoding="utf-8") as f:
            daily_events = json.load(f)

    known_keys = {f"{e['date']}T{e['time']}" for e in daily_events}

    for item in xml_root.findall(".//item"):
        desc = item.findtext("description")
        parsed = parse_description(desc)
        if not parsed:
            continue

        timestamp = f"{parsed['date']}T{parsed['time']}"
        if timestamp in known_keys:
            print(f"⚠️ Skipped duplicate or old event: {timestamp}")
            continue

        parsed["city"] = reverse_geocode(parsed["lat"], parsed["lon"])
        daily_events.append(parsed)
        known_keys.add(timestamp)
        print(f"📦 Appending new event to {local_tmp_file}: {timestamp} | {parsed['city']}")

    if daily_events:
        with open(local_tmp_file, "w", encoding="utf-8") as f:
            json.dump(daily_events, f, ensure_ascii=False, indent=2)

        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(daily_events, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json"
            )
            print(f"✅ Uploaded to S3: {s3_key} ({len(daily_events)} events)")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
    else:
        print("ℹ️ No new events to upload.")

def main():
    root = fetch_xml()
    parse_and_upload(root)

if __name__ == "__main__":
    while True:
        try:
            print(f"\n🔁 Polling at {datetime.utcnow().isoformat()}Z")
            main()
        except Exception as e:
            print(f"❌ Σφάλμα: {e}")
        time.sleep(POLL_INTERVAL)
