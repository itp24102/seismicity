import os
import json
import logging
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def handler(event, context):
    logging.info("📡 Influx Writer ενεργοποιήθηκε")
    logging.info("📥 Event received:")
    logging.info(json.dumps(event))

    influx_url = os.environ.get("INFLUX_URL")
    influx_token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG", "seismicity")
    bucket = os.environ.get("INFLUX_BUCKET", "seismicity")

    logging.info(f"🔧 ENV -> URL: {influx_url}, ORG: {org}, BUCKET: {bucket}")

    events = event.get("events", [])
    lines = []

    for e in events:
        try:
            timestamp = int(datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp())
            line = (
                f"earthquake,"
                f"location={escape_tag(e['location'])} "
                f"depth={e['depth']},"
                f"latitude={e['lat']},"
                f"longitude={e['lon']},"
                f"magnitude={e['magnitude']} "
                f"{timestamp}"
            )
            lines.append(line)
            logging.info(f"🧪 Line Protocol: {line}")
        except Exception as ex:
            logging.error(f"❌ Σφάλμα σε εγγραφή: {e} ➜ {ex}")

    if lines:
        try:
            with InfluxDBClient(url=influx_url, token=influx_token, org=org) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                logging.info(f"📤 Writing {len(lines)} points...")
                write_api.write(bucket=bucket, org=org, record=lines, write_precision='s')
                logging.info(f"✅ Καταχωρήθηκαν {len(lines)} σημεία στο InfluxDB.")
        except Exception as e:
            logging.error(f"❌ Σφάλμα κατά την αποστολή στο InfluxDB: {e}")
    else:
        logging.warning("⚠️ Δεν υπάρχουν σημεία προς αποστολή.")

def escape_tag(value):
    return (
        value.replace("\\", "\\\\")
             .replace(" ", "\\ ")
             .replace(",", "\\,")
             .replace("=", "\\=")
    )
