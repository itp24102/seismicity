## `seismicity/services/` 

The services directory contains the source code and Docker configurations for all microservices and functions in the seismicity project. Each subfolder under `services/` represents a distinct component of the system. The project follows a microservice architecture, where each service has a specific role in the overall data processing pipeline for seismic events.

Key services (subdirectories) include:

-   **Poller** (`services/poller`): This is an AWS Lambda function responsible for fetching seismic data from an external API. It periodically queries the European seismic data feed (SeismicPortal API) for recent earthquake events. The Poller function performs tasks like reverse geocoding coordinates to location names and filtering new events. After collecting new seismic event data, the Poller stores a record in S3 and then triggers the next service (Influx Writer) asynchronously[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/poller/src/handler.py). This service is implemented as a Python AWS Lambda (see `handler.py`) and is deployed via Terraform and Jenkins (no Docker container since it runs on AWS Lambda).
    
-   **Influx Writer** (`services/influx-writer`): This is another AWS Lambda function that takes seismic events (usually passed from the Poller) and writes them into the InfluxDB time-series database. It receives a batch of events (via the Poller’s invocation), formats them into InfluxDB’s line protocol, and inserts them into the **InfluxDB** instance. This allows the data to be stored with timestamps and queried for visualization. The Influx Writer uses the InfluxDB Python client to communicate with the database. Like Poller, it’s an AWS Lambda function (defined in `influx_writer.py`) and is deployed via CI/CD (packaged as a ZIP and applied with Terraform).
    
-   **Ingest** (`services/ingest`): _Planned (Kubernetes Service)._ The ingest service is intended to run on the Kubernetes cluster and act as an entry point for data ingestion within the cluster’s ecosystem. In a future implementation, it might receive data (perhaps from webhooks, devices, or other sources) and feed it into the processing pipeline. Right now, this service is a **placeholder** – the code simply starts up and waits (no real logic yet)[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/ingest/src/main.py). It has a Dockerfile[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/ingest/Dockerfile) and a Kubernetes Deployment manifest prepared, so when development is completed, it can be built into an image and deployed via ArgoCD.
    
-   **Processor** (`services/processor`): _Planned (Kubernetes Service)._ The processor service is meant to take data from the ingest service (or directly from Poller in an extended design) and perform any computational processing or analysis on the seismic data. For example, it could filter events, calculate additional metrics, or transform the data. As of now, this service is also a placeholder with scaffolding in place but no concrete logic implemented yet.
    
-   **Notifier** (`services/notifier`): _Planned (Kubernetes Service)._ The notifier service would be responsible for sending out notifications or alerts based on the seismic data. For instance, if a significant earthquake is detected (above a certain magnitude or in a specific region), the notifier could email users or send messages. Currently, this service is a placeholder (no real notification logic). It stands ready in the codebase to be expanded with features like connecting to an email/SMS service or push notifications. It has a Deployment manifest and basic code structure set up similarly to ingest and processor.
    

**Common structure:** Each service directory typically contains:

-   A `src/` folder with the service’s source code (e.g., the Poller has `src/handler.py`, Influx Writer has `src/influx_writer.py`, Ingest has `src/main.py`, etc.).
    
-   A `Dockerfile` if the service is intended to run in a container (ingest/processor/notifier have Dockerfiles to define their container image, whereas poller and influx-writer do not since they run on AWS Lambda).
    
-   A `Jenkinsfile` defining how to build and deploy that service. For container services, the Jenkinsfile would describe building the Docker image and pushing it. For the Lambda services, it describes zipping the code and deploying via AWS (including Terraform steps as needed).
    
-   A `requirements.txt` or similar, if the service has Python dependencies that need to be installed (Poller and Influx Writer, for example, list libraries like `requests`, `boto3`, `influxdb-client`, `geopy` in their requirements).
    

**How these services work together:** The design is that the **Poller** and **Influx Writer** handle the automated retrieval and storage of seismic data, forming the data pipeline’s core. The Poller fetches new events and triggers the Influx Writer to save them, as described above. The other three services (Ingest, Processor, Notifier) are structured to potentially form a second pipeline:

-   The **Ingest** service could receive or aggregate data (either from Poller or another source) and hand it off to the Processor.
    
-   The **Processor** would perform computations or filtering.
    
-   The **Notifier** would act on processed data (sending alerts).  
    In the current state, however, this in-cluster pipeline isn’t active – these services are stubs awaiting implementation. The main active data flow is via the Poller → InfluxWriter Lambdas and the data visualization in Grafana.
    

This microservice separation ensures each component is focused and can be developed and scaled independently. As development continues, new services can be added under `services/` following the same pattern (with their own Dockerfile, Jenkinsfile, and manifests in `deployments/`). Developers can work on one part of the pipeline without affecting others, and the CI/CD process will deploy updates for that service when ready.