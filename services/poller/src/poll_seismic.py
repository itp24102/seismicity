import os
import requests
import boto3
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Περιβάλλον
URL = "http://www.geophysics.geol.uoa.gr/stations/maps/seismicity.xml"
S3_BUCKET = os.environ.get("S3_BUCKET", "seismicity-app-bucket")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

geolocator = Nominatim(user_agent="seismicity-poller")

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="el", timeout=10)
        return location.raw.get('address', {}).get('city', 'Άγνωστη') if location else "Άγνωστη"
    except GeocoderTimedOut:
        return "Άγνωστη"

def fetch_xml():
    response = requests.get(URL)
    response.raise_for_status()
    return ET.fromstring(response.content)

def parse_and_upload(xml_root):
    s3 = boto3.client("s3", region_name=AWS_REGION)

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
            continue

        # Timestamp ISO μορφής
        timestamp = f"{data['date']}T{data['time']}"
        try:
            iso_ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").isoformat()
        except ValueError:
            continue

        # Ανάκτηση πόλης
        data["city"] = reverse_geocode(data["lat"], data["lon"])

        # Δημιουργία JSON αρχείου και αποθήκευση σε S3
        s3_key = f"{S3_KEY_PREFIX}{iso_ts}.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(data),
            ContentType="application/json"
        )
        print(f"✅ Uploaded: {s3_key} | {data['city']}")

def main():
    root = fetch_xml()
    parse_and_upload(root)

if __name__ == "__main__":
    main()
