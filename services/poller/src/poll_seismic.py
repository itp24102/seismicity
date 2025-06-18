import os
import time
import requests
import boto3
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeopyError

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

def fetch_xml():
    print(f"📥 Fetching data from {URL}")
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return ET.fromstring(response.content)

def parse_description(desc):
    try:
        desc = desc.replace("<br>", "\n").replace("&lt;br&gt;", "\n")
        fields = dict(re.findall(r"(Latitude|Longitude|Depth|Time|M)[:]?\s*([^\n]+)", desc))

        lat_raw = fields.get("Latitude", "0").replace("N", "").strip()
        lon_raw = fields.get("Longitude", "0").replace("E", "").strip()

        lat = float(lat_raw)
        lon = float(lon_raw)
        depth = fields.get("Depth", "0").replace("km", "").strip()
        mag = fields.get("M", "0").strip()
        timestamp = datetime.strptime(fields.get("Time", "1970-01-01 00:00:00"), "%d-%b-%Y %H:%M:%S")

        return {
            "timestamp": timestamp.isoformat(),
            "lat": lat,
            "lon": lon,
            "depth": depth,
            "mag": mag,
        }
    except Exception as e:
        print(f"⚠️ Failed to parse description: {desc}\n{e}")
        return None

def parse_and_upload(xml_root):
    channel = xml_root.find("channel")
    if channel is None:
        print("⚠️ No <channel> found in XML")
        return

    for item in channel.findall("item"):
        desc = item.findtext("description")
        if not desc:
            continue

        parsed = parse_description(desc)
        if not parsed:
            continue

        city = reverse_geocode(parsed['lat'], parsed['lon'])
        parsed["city"] = city

        s3_key = f"{S3_KEY_PREFIX}{parsed['timestamp']}.json"
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(parsed, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json"
            )
            print(f"✅ Uploaded: {s3_key} | Πόλη: {city}")
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")

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
