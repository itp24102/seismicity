import os
import time
import requests
import boto3
import xml.etree.ElementTree as ET
from datetime import datetime
from geopy.distance import geodesic

URL = "http://www.geophysics.geol.uoa.gr/stations/maps/recent_eq_1d_el.xml"

S3_BUCKET = os.environ.get("S3_BUCKET", "seismicity-app-bucket")
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "events/")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))  # default: every 5 minutes

# List of known cities with coordinates
CITIES = {
    "Αθήνα": (37.9838, 23.7275),
    "Θεσσαλονίκη": (40.6401, 22.9444),
    "Πάτρα": (38.2466, 21.7346),
    "Ηράκλειο": (35.3387, 25.1442),
    "Λάρισα": (39.639, 22.4191),
    "Βόλος": (39.361, 22.9425),
    "Ιωάννινα": (39.665, 20.8537),
    "Τρίκαλα": (39.5557, 21.7679),
    "Χαλκίδα": (38.4636, 23.6021),
    "Σέρρες": (41.085, 23.5479),
    "Αλεξανδρούπολη": (40.8457, 25.8736),
    "Καλαμάτα": (37.0389, 22.1142),
    "Καβάλα": (40.9369, 24.4126),
    "Κατερίνη": (40.2696, 22.5061),
    "Χανιά": (35.5138, 24.018),
    "Λαμία": (38.9, 22.4333),
    "Ρόδος": (36.434, 28.2176),
    "Κομοτηνή": (41.1175, 25.4058),
    "Ξάνθη": (41.1349, 24.888),
    "Αγρίνιο": (38.6218, 21.407),
    "Δράμα": (41.1496, 24.1472),
    "Βέροια": (40.5244, 22.2012),
    "Κέρκυρα (πόλη)": (39.62, 19.92),
    "Γιαννιτσά": (40.7919, 22.4072),
    "Ρέθυμνο": (35.3644, 24.4821),
}

def fetch_earthquake_data():
    response = requests.get(URL)
    response.raise_for_status()
    return ET.fromstring(response.content)

def find_closest_city(lat, lon):
    quake_location = (lat, lon)
    closest_city = min(CITIES.items(), key=lambda city: geodesic(quake_location, city[1]).km)
    return closest_city[0]

def parse_and_upload_to_s3(xml_root):
    s3 = boto3.client("s3", region_name=AWS_REGION)
    for event in xml_root.findall("event"):
        event_data = {
            "date": event.findtext("date"),
            "time": event.findtext("time"),
            "lat": event.findtext("lat"),
            "lon": event.findtext("lon"),
            "depth": event.findtext("depth"),
            "mag": event.findtext("mag"),
            "region": event.findtext("region"),
        }

        if not all(event_data.values()):
            continue

        event_id = f"{event_data['date']}T{event_data['time'].replace(':', '')}_{event_data['lat']}_{event_data['lon']}"
        lat = float(event_data["lat"])
        lon = float(event_data["lon"])
        event_data["closest_city"] = find_closest_city(lat, lon)
        timestamp = datetime.strptime(f"{event_data['date']} {event_data['time']}", "%Y-%m-%d %H:%M:%S").isoformat()
        event_data["timestamp"] = timestamp

        # Construct filename and key
        filename = f"{event_id}.json"
        key = f"{S3_KEY_PREFIX}{filename}"

        # Upload to S3
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=str(event_data),
            ContentType="application/json"
        )
        print(f"[✔] Uploaded event {event_id} to s3://{S3_BUCKET}/{key}")

def main():
    print(f"[✓] Starting poller for {URL}")
    while True:
        try:
            xml_root = fetch_earthquake_data()
            parse_and_upload_to_s3(xml_root)
        except Exception as e:
            print(f"[!] Error during poll: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
