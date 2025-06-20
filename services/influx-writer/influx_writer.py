# influx_writer.py
import os
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "seismicity")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "seismicity")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def handler(event, context):
    print("📡 Influx Writer ενεργοποιήθηκε")
    events = event.get("events", [])
    if not events:
        print("⚠️ Δεν ελήφθησαν σεισμικά δεδομένα.")
        return {"statusCode": 400, "body": "No events provided"}

    points = []
    for e in events:
        try:
            timestamp = e.get("timestamp")
            if not timestamp:
                print(f"⚠️ Event χωρίς timestamp: {e}")
                continue

            time = datetime.fromisoformat(timestamp.replace("Z", ""))

            point = (
                Point("earthquake")
                .tag("location", e.get("location", "Άγνωστη"))
                .field("magnitude", float(e.get("magnitude", 0)))
                .field("depth", float(e.get("depth", 0)))
                .field("lat", float(e.get("lat", 0)))
                .field("lon", float(e.get("lon", 0)))
                .time(time, WritePrecision.NS)
            )
            points.append(point)
        except Exception as ex:
            print(f"❌ Σφάλμα μετατροπής σεισμού: {ex}")
            print(json.dumps(e, ensure_ascii=False, indent=2))

    try:
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print(f"✅ Καταχωρήθηκαν {len(points)} σημεία στο InfluxDB.")
        return {"statusCode": 200, "body": f"Wrote {len(points)} events"}
    except Exception as ex:
        print(f"❌ Σφάλμα κατά την εγγραφή στο InfluxDB: {ex}")
        return {"statusCode": 500, "body": "InfluxDB write error"}
