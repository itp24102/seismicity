FROM python:3.11-slim
WORKDIR /app
RUN pip install feedparser geopy boto3
COPY src/poll_seismic.py .
CMD ["python", "poll_seismic.py"]
