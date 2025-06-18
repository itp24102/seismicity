import os
import time
import json
import boto3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeopyError

# === Περιβάλλον ===
URL = "http://www.geophysics.geol.uoa.gr/stations/maps/seismicity.xml"
S3_BUCKET = os.environ.get("S3_BUCKET", "seismicity-app-bucket")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))

# === S3 ===
s3 = boto3.client("s3", region_name=AWS_REGION)

# === Geolocator ===
geolocator = Nominatim(user_agent="seismicity-poller")

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="el", timeout=10)
        return location.raw.get('address', {}).get('city', 'Άγνωστη') if location else "Άγνωστη"
    except (GeocoderTimedOut, GeopyError) as e:
        print(f"⚠️ Geocoding failed for ({lat}, {lon}): {e}")
        return "Άγνωστη"

def fetch_xml():
    print(f"📥 Fetching XML from {URL}")
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return ET.fromstring(response.content)

def extract_data(item):
    try:
        title = item.findtext("title", "")
        description = item.findtext("description", "").replace("&lt;br&gt;", "\n")
        pub_date = item.findtext("pubDate", "")
        guid = item.findtext("guid", "")

        # Title: M 1.2, 18/06 - 22:30:12 UTC, Some Location
        parts = title.split(",")
        magnitude = parts[0].replace("M", "").strip()
        dt_str = parts[1].split("UTC")[0].strip()
        dt_iso = datetime.strptime(f"2025-{dt_str}", "%Y-%d/%m - %H:%M:%S").isoformat()

        lines = description.splitlines()
        location = lines[0].strip()
        lat = lines[1].split(":")[1].strip().replace("N", "")
        lon = lines[2].split(":")[1].strip().replace("E", "")
        depth = lines[3].split(":")[1].strip().replace("km", "")

        city = reverse_geocode(lat, lon)

        return {
            "guid": guid,
            "timestamp": dt_iso,
            "magnitude": magnitude,
            "lat": lat,
            "lon": lon,
            "depth": depth,
            "location": location,
            "city": city,
        }
    except Exception as e:
        print(f"⚠️ Failed to parse item: {e}")
        return None

def load_existing_guids(s3_key):
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        events = json.loads(obj["Body"].read().decode("utf-8"))
        return set(event.get("guid") for event in events)
    except s3.exceptions.NoSuchKey:
        return set()
    except Exception as e:
        print(f"❌ Failed to load existing data from {s3_key}: {e}")
        return set()

def save_events(events, s3_key):
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(events, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json"
        )
        print(f"✅ Updated S3: {s3_key} with {len(events)} events")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")

def parse_and_upload(xml_root):
    items = xml_root.findall(".//item")
    new_events = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    s3_key = f"{S3_KEY_PREFIX}{today}.json"
    existing_guids = load_existing_guids(s3_key)

    for item in items:
        event = extract_data(item)
        if not event or event["guid"] in existing_guids:
            continue
        new_events.append(event)

    if new_events:
        print(f"📦 Found {len(new_events)} new events")
        combined_events = list(existing_guids) + new_events
        save_events(new_events + list(existing_guids), s3_key)
    else:
        print("ℹ️ No new events found")

def main():
    xml_root = fetch_xml()
    parse_and_upload(xml_root)

if __name__ == "__main__":
    while True:
        print(f"\n🔁 Polling at {datetime.utcnow().isoformat()}Z")
        try:
            main()
        except Exception as e:
            print(f"❌ Σφάλμα: {e}")
        time.sleep(POLL_INTERVAL)
