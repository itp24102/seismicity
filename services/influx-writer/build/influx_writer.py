import os
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision

INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

def parse_iso_timestamp(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

def handler(event, context):
    print("📡 Influx Writer ενεργοποιήθηκε")
    print(f"📥 Event received:\n{json.dumps(event, ensure_ascii=False)}")
    print(f"🔧 ENV -> URL: {INFLUX_URL}, ORG: {INFLUX_ORG}, BUCKET: {INFLUX_BUCKET}")

    events = event.get("events", [])
    write_api = client.write_api()
    points = []

    for e in events:
        try:
            t = parse_iso_timestamp(e["timestamp"])

            point = (
                Point("earthquake")
                .tag("location", e["location"])
                .field("magnitude", float(e["magnitude"]))
                .field("depth", float(e["depth"]))
                .field("latitude", float(e["lat"]))
                .field("longitude", float(e["lon"]))
                .time(t, WritePrecision.S)  # <== Αλλαγή εδώ
            )
            print(f"🧪 Line Protocol: {point.to_line_protocol()}")
            points.append(point)
        except Exception as ex:
            print(f"❌ Σφάλμα μετατροπής σεισμού: {ex}")
            print(json.dumps(e, ensure_ascii=False, indent=2))

    if points:
        print(f"📤 Writing {len(points)} points...")
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print(f"✅ Καταχωρήθηκαν {len(points)} σημεία στο InfluxDB.")
    else:
        print("ℹ️ Δεν υπάρχουν έγκυρα σημεία προς καταχώρηση.")
