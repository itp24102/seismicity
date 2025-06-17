import feedparser
import boto3
import json
from datetime import datetime
from geopy.distance import geodesic

# AWS S3 configuration
S3_BUCKET = "seismicity-app-bucket"

# List of major Greek cities with their geographic coords
GREEK_CITIES = [
    {"name": "Αθήνα", "latitude": 37.9838, "longitude": 23.7275},
    {"name": "Θεσσαλονίκη", "latitude": 40.6401, "longitude": 22.9444},
    {"name": "Πάτρα", "latitude": 38.2466, "longitude": 21.7346},
    {"name": "Ηράκλειο", "latitude": 35.3387, "longitude": 25.1442},
    {"name": "Λάρισα", "latitude": 39.639, "longitude": 22.4191},
    {"name": "Βόλος", "latitude": 39.361, "longitude": 22.9425},
    {"name": "Ιωάννινα", "latitude": 39.665, "longitude": 20.8537},
    {"name": "Τρίκαλα", "latitude": 39.5557, "longitude": 21.7679},
    {"name": "Χαλκίδα", "latitude": 38.4636, "longitude": 23.6021},
    {"name": "Σέρρες", "latitude": 41.085, "longitude": 23.5479},
    {"name": "Αλεξανδρούπολη", "latitude": 40.8457, "longitude": 25.8736},
    {"name": "Καλαμάτα", "latitude": 37.0389, "longitude": 22.1142},
    {"name": "Καβάλα", "latitude": 40.9369, "longitude": 24.4126},
    {"name": "Κατερίνη", "latitude": 40.2696, "longitude": 22.5061},
    {"name": "Χανιά", "latitude": 35.5138, "longitude": 24.018},
    {"name": "Λαμία", "latitude": 38.9, "longitude": 22.4333},
    {"name": "Ρόδος", "latitude": 36.434, "longitude": 28.2176},
    {"name": "Κομοτηνή", "latitude": 41.1175, "longitude": 25.4058},
    {"name": "Ξάνθη", "latitude": 41.1349, "longitude": 24.888},
    {"name": "Αγρίνιο", "latitude": 38.6218, "longitude": 21.407},
    {"name": "Δράμα", "latitude": 41.1496, "longitude": 24.1472},
    {"name": "Βέροια", "latitude": 40.5244, "longitude": 22.2012},
    {"name": "Κέρκυρα (πόλη)", "latitude": 39.62, "longitude": 19.92},
    {"name": "Γιαννιτσά", "latitude": 40.7919, "longitude": 22.4072},
    {"name": "Ρέθυμνο", "latitude": 35.3644, "longitude": 24.4821},
]

def find_closest_city(lat, lon):
    """Returns the closest city from GREEK_CITIES to a given point."""
    min_dist = float('inf')
    closest = None
    for city in GREEK_CITIES:
        city_coords = (city['latitude'], city['longitude'])
        dist = geodesic((lat, lon), city_coords).kilometers
        if dist < min_dist:
            min_dist = dist
            closest = city
    return closest, min_dist

def fetch_seismic_data(url="http://www.geophysics.geol.uoa.gr/stations/maps/seismicity.xml"):
    """Parses RSS feed of earthquakes."""
    feed = feedparser.parse(url)
    earthquakes = []

    for entry in feed.entries:
        coords = entry.georss_point.split()
        lat = float(coords[0]) 
        lon = float(coords[1])

        city, distance = find_closest_city(lat, lon)

        earthquakes.append({ 
            "id": entry.id,
            "time": entry.published,
            "latitude": lat,
            "longitude": lon,
            "magnitude": float(entry.title.split()[1]),
            "depth": float(entry.summary.split()[2]),
            "closest_city": city['name'],
            "distance_km": distance
        })
    return earthquakes

def store_to_s3(earthquake):
    """Saves earthquake data to S3 in JSON format."""
    s3 = boto3.client('s3')
    date = datetime.utcnow().date()
    key = f"{date}/{earthquake['id']}.json"

    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(earthquake))
    print(f"Stored {earthquake['id']} to s3://{S3_BUCKET}/{key}")

def main():
    """Main pipeline."""
    earthquakes = fetch_seismic_data()
    for eq in earthquakes:
        store_to_s3(eq)

if __name__ == "__main__":
    main()
