import os
import json
import sys
import logging
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from dateutil.parser import isoparse

# Explicit basicConfig για AWS Lambda (stdout logging)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s\t%(asctime)s\t%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Χρησιμοποίησε logger αντί για logging
def handler(event, context):
    logger.info("📡 Influx Writer ενεργοποιήθηκε")
    logger.info("📥 Event received:")
    logger.info(json.dumps(event))

    influx_url = os.environ.get("INFLUX_URL")
    influx_token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG", "seismicity")
    bucket = os.environ.get("INFLUX_BUCKET", "seismicity")

    logger.info(f"🔧 ENV -> URL: {influx_url}, ORG: {org}, BUCKET: {bucket}")

    events = event.get("events", [])
    lines = []

    for e in events:
        try:
            timestamp = int(isoparse(e["timestamp"]).timestamp())
            line = (
                f"earthquake,"
                f"location={escape_tag(e['location'])} "
                f"depth={e['depth']},"
                f"latitude={e['latitude']},"
                f"longitude={e['longitude']},"
                f"magnitude={e['magnitude']} "
                f"{timestamp}"
            )
            lines.append(line)
            logger.info(f"🧪 Line Protocol: {line}")
        except Exception as ex:
            logger.error(f"❌ Σφάλμα σε εγγραφή: {e} ➜ {ex}")

    if lines:
        try:
            with InfluxDBClient(url=influx_url, token=influx_token, org=org) as client:
                write_api = client.write_api(write_options=SYNCHRONOUS)
                logger.info(f"📤 Writing {len(lines)} points...")
                write_api.write(bucket=bucket, org=org, record=lines, write_precision='s')
                logger.info(f"✅ Καταχωρήθηκαν {len(lines)} σημεία στο InfluxDB.")
        except Exception as e:
            logger.error(f"❌ Σφάλμα κατά την αποστολή στο InfluxDB: {e}")
    else:
        logger.warning("⚠️ Δεν υπάρχουν σημεία προς αποστολή.")

def escape_tag(value):
    return (
        value.replace("\\", "\\\\")
             .replace(" ", "\\ ")
             .replace(",", "\\,")
             .replace("=", "\\=")
    )
