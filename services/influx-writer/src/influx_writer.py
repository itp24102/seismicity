import os
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision

INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")

print(f"🔌 Connecting to InfluxDB at {INFLUX_URL}...")
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    if client.ping():
        print("✅ Επικοινωνία με InfluxDB: OK")
    else:
        print("❌ Σφάλμα σύνδεσης με InfluxDB")
except Exception as ex:
    print(f"❌ Αποτυχία σύνδεσης στο InfluxDB: {ex}")
    raise ex

def parse_iso_timestamp(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

def handler(event, context):
    print("📡 Influx Writer ενεργοποιήθηκε")

    events = event.get("events", [])
    if not events:
        print("ℹ️ Δεν υπάρχουν δεδομένα για αποστολή.")
        return

    write_api = client.write_api()
    points = []

    for e in events:
        try:
            t = parse_iso_timestamp(e["timestamp"])

            # 🛠 DEBUG: Προσθέτουμε -debug στο location
            location = e.get("location", "unknown") + " -debug"

            point = (
                Point("earthquake")
                .tag("location", location)
                .field("magnitude", float(e["magnitude"]))
                .field("depth", float(e["depth"]))
                .field("latitude", float(e["lat"]))
                .field("longitude", float(e["lon"]))
                .time(t, WritePrecision.NS)
            )
            points.append(point)
        except Exception as ex:
            print(f"❌ Σφάλμα μετατροπής σεισμού: {ex}")
            print(json.dumps(e, ensure_ascii=False, indent=2))

    try:
        if points:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
            print(f"✅ Καταχωρήθηκαν {len(points)} σημεία στο InfluxDB.")
        else:
            print("ℹ️ Δεν υπάρχουν έγκυρα σημεία προς καταχώρηση.")
    except Exception as ex:
        print(f"❌ Σφάλμα κατά την εγγραφή στο InfluxDB: {ex}")
