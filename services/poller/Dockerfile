# Dockerfile for the Seismicity Poller Service 
FROM python:3.11-slim

WORKDIR /app

# Εγκατάσταση requirements
RUN pip install feedparser geopy boto3 requests

# Αντιγραφή αρχείου
COPY src/poll_seismic.py .

# Εκκίνηση
CMD ["python3", "poll_seismic.py"]
