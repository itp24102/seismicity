
# Seismicity – Earthquake Data Monitoring Platform

**Seismicity** is a comprehensive platform for collecting, processing, and visualizing seismic activity data (earthquakes). It leverages a modern microservices architecture spanning cloud services and a Kubernetes cluster, with full DevOps automation. The goal of the project is to continuously fetch real-time earthquake data and make it easily accessible through dashboards and alerts for end-users or researchers interested in seismic events.

## Overview and Purpose

Seismicity is designed to automate the flow of seismic data from acquisition to presentation. The system periodically retrieves earthquake event data from external sources (such as the European-Mediterranean Seismological Centre’s API) and stores that data for analysis and monitoring. The purpose is to provide a near real-time view of seismic events in a specified region (e.g. for Greece and surrounding areas, as configured in the data fetcher) and eventually notify stakeholders of significant events.

The platform is beginner-friendly and heavily documented, making it a great example of integrating multiple modern technologies:

-   **Data Collection:** Automatically poll an external seismic data source for new earthquake information.
    
-   **Data Processing:** Structure and enrich the data (e.g., add location names via reverse geocoding, filter duplicates).
    
-   **Data Storage:** Save the data in a time-series database for historical tracking.
    
-   **Visualization:** Provide dashboards (Grafana) where users can see earthquake occurrences on timelines, magnitudes, and other metrics.
    
-   **Alerting (planned):** In future iterations, send alerts for large events or patterns (via email, SMS, etc., using the Notifier service).
    

In summary, Seismicity serves as both a practical earthquake monitoring tool and a demonstration of a cloud-native, multi-cloud application deployment.

## High-Level Architecture

The Seismicity project’s architecture consists of several interconnected components, each responsible for a layer of the system’s functionality. Here’s a high-level breakdown:

-   **AWS Lambda Functions (Serverless Microservices):** The project uses two Lambda functions for core data tasks:
    
    -   _Poller Lambda:_ Periodically calls the external seismic API to fetch new earthquake events. Runs on AWS on a schedule (could be triggered by a CloudWatch Event/cron or invoked manually via Jenkins for now).
        
    -   _Influx Writer Lambda:_ Receives event data (from the Poller) and writes it to the InfluxDB database.  
        These functions allow the data ingestion to scale and run independently without managing servers for these tasks.
        
-   **Azure Virtual Machine & MicroK8s (Kubernetes Cluster):** An Azure VM (Ubuntu) hosts a lightweight Kubernetes cluster (MicroK8s). This is the control center for our supporting services:
    
    -   The **Jenkins CI/CD server** runs here (in a Kubernetes pod) to handle builds and deployments.
        
    -   **ArgoCD (GitOps)** operates here to automatically deploy any changes from the `deployments/` manifests to the cluster.
        
    -   **Monitoring tools** like Prometheus and Grafana run on this cluster. Grafana provides a web UI for viewing dashboards, and Prometheus (with Node Exporter, etc.) can monitor the health of the VM and cluster.
        
    -   (Planned) Additional microservices (Ingest, Processor, Notifier) will run as deployments on this Kubernetes cluster, making use of the cluster’s networking and scalability.
        
-   **Infrastructure as Code:** The foundation is managed through code:
    
    -   Terraform (via **OpenTofu**) scripts set up all necessary cloud infrastructure on both AWS and Azure. For instance, it creates the Azure VM and networking, the AWS Lambdas, IAM roles, S3 bucket, etc., so that the environment can be reproduced or scaled easily.
        
    -   **Ansible automation** then configures the Azure VM: installing MicroK8s, Docker, and deploying the required software (Jenkins, Grafana, etc.) into the cluster using Helm charts. This means a new VM can be provisioned and configured with minimal manual steps.
        
-   **Data Storage – InfluxDB:** An InfluxDB instance is running (on the Azure VM, accessible on port 8086) as the time-series database. It stores all incoming seismic events with their timestamp, magnitude, location, etc. This database is optimized for time-stamped data and allows for efficient querying and downsampling of historical events.
    
-   **Visualization – Grafana:** Grafana is deployed on the Kubernetes cluster (accessible via a NodePort or potentially an ingress). It’s configured to use InfluxDB as a data source. A pre-built dashboard displays recent earthquakes and possibly system metrics. Users can see graphs of earthquake frequency, magnitudes over time, or geographical distribution (if integrated with a world map panel, for example).
    
-   **Continuous Integration/Deployment:** The CI/CD pipeline ensures that when code changes or new features are added:
    
    -   Jenkins will rebuild applications or Docker images, run tests (if any), and deploy updates.
        
    -   ArgoCD will pick up changes in Kubernetes manifests and synchronize them.
        
    -   Terraform/Ansible changes can be applied through Jenkins jobs as well, keeping the infrastructure aligned with the codebase.
        
-   **Networking & Access:** The Azure VM has a public DNS (`seismicity.westeurope.cloudapp.azure.com`) and is locked down to specific ports via its Network Security Group. Jenkins (NodePort 32000), Prometheus (32001), and Grafana (32002) are reachable through these ports in a browser for administrators. InfluxDB’s port 8086 can be used by the Lambdas or other services to write data (but is typically not exposed to the public for security). SSH (port 22) is open for maintenance on the VM. By using NodePorts and the VM’s IP, we avoid needing a load balancer or cloud-specific Kubernetes service for these internal tools, while still allowing convenient access when needed[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/azure/main.tf)[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/azure/main.tf).
    

Overall, the architecture is **distributed** across AWS (for serverless functions) and Azure (for the Kubernetes cluster and DB). This multi-cloud approach demonstrates flexibility – for example, AWS is leveraged for its Lambda capabilities, while Azure provides an easy VM environment for a persistent server and cluster.

## Technologies Used

The project brings together a variety of modern technologies and tools, each serving a specific purpose:

-   **OpenTofu (Terraform)** – Used for Infrastructure as Code. OpenTofu scripts automate the creation of cloud resources on AWS and Azure. Instead of clicking in cloud consoles, all infrastructure (VMs, networks, Lambdas, etc.) is defined in code and can be version controlled. (OpenTofu is a community-driven fork of Terraform, ensuring compatibility with Terraform providers.)
    
-   **Ansible** – Used for configuration management after provisioning. Ansible playbooks automate installing software and configuring the system on the Azure VM. For example, Ansible installs MicroK8s, sets up Docker, and deploys Helm charts for Jenkins, Prometheus, and Grafana. This ensures a consistent setup and saves time on manual server configuration.
    
-   **Docker** – Containerization for services. Services like ingest, processor, and notifier are containerized with Docker, allowing them to run anywhere (locally via Docker Compose, or in Kubernetes). Docker ensures that each service has a consistent environment with its dependencies.
    
-   **Kubernetes (MicroK8s)** – Orchestrates containerized services. MicroK8s is a slim Kubernetes distribution that runs on a single node (our Azure VM). It manages the lifecycle of our in-cluster services (ingest, processor, notifier, Jenkins, Grafana, etc.), handling scheduling, restarts, and service discovery between them.
    
-   **ArgoCD** – GitOps continuous deployment tool. ArgoCD watches the git repository (specifically the `deployments/` directory) for any changes to Kubernetes manifest files. Whenever you update or add a manifest (for example, tweak a Deployment or add a new service), ArgoCD will apply those changes to the Kubernetes cluster automatically. This provides a declarative deployment model and easy rollback (by reverting git changes).
    
-   **Jenkins** – Continuous Integration/Continuous Deployment server. Jenkins automates building and deploying the code. We use it to:
    
    -   Run pipelines defined in Jenkinsfiles for each service.
        
    -   Build Docker images and push them to GHCR.
        
    -   Package and deploy AWS Lambda functions (including running Terraform to update infrastructure).
        
    -   Overall, it’s the automation hub that turns code changes into running services or functions.
        
-   **GitHub Container Registry (GHCR)** – Hosts Docker images for the project’s services. Built images (e.g., `ingest:latest`, `processor:latest`, etc.) are pushed to GHCR under the repository’s namespace. The Kubernetes cluster is configured to pull images from this registry (using a secret for authentication).
    
-   **AWS Lambda** – Serverless computing service used for the Poller and Influx Writer functions. It runs code in response to events (or on schedule) without needing to manage servers. This is ideal for the Poller (which might run every few minutes) and decouples data fetching from the rest of the system.
    
-   **AWS S3** – Cloud storage used by the Poller Lambda to store interim data (daily JSON files of events). It ensures that the Poller can keep track of already seen events and pass data reliably to the next stage.
    
-   **AWS IAM** – Security service for managing roles/permissions. The Lambdas run with IAM Roles that grant them permission (for example, Poller’s role allows writing to S3 and invoking the InfluxWriter Lambda[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/poller/Jenkinsfile)).
    
-   **InfluxDB** – A time-series database for storing seismic event data. InfluxDB is well-suited for time-stamped data like earthquake events. We use InfluxDB 2.x (which uses a token-based auth) to store events with fields like magnitude, depth, and tags like location. This database allows Grafana to query and plot the data over time.
    
-   **Grafana** – Visualization and dashboard service. Grafana connects to InfluxDB and provides interactive dashboards. We have configured it with a dashboard that shows the seismic events (for example, a time-series graph of earthquake magnitudes, counts per day, or even a map if configured). Grafana makes the data accessible and interpretable to users without needing to run database queries.
    
-   **Prometheus & Monitoring Stack** – Prometheus is deployed to gather metrics, mainly for infrastructure (like CPU, memory of the VM, and Kubernetes cluster metrics). It’s part of the monitoring stack and can feed data into Grafana dashboards (e.g., for cluster health). This ensures the platform’s health is also being monitored.
    
-   **Python** – The primary programming language used for the microservices (Poller, InfluxWriter, etc.). Python’s ecosystem (requests for HTTP, boto3 for AWS, influxdb-client for Influx, etc.) powers the data logic.
    
-   **Geopy (Nominatim)** – A library (used in Poller) for reverse geocoding latitude/longitude to human-readable locations. This adds context to each earthquake event (e.g., “Athens, Greece” instead of just coordinates).
    
-   **GitHub (Git)** – All code and configurations are stored in a Git monorepo (this repository). Git provides version control, collaboration, and triggers for CI/CD (webhooks to Jenkins or pull requests for code reviews). The monorepo structure means everything – from backend code to infrastructure code – lives in one place for easier tracking.
    

By combining these technologies, Seismicity achieves a robust, automated workflow from code to production deployment, and from raw data to useful insights, all while being relatively easy to maintain and extend.

## Deployment and Automation Flow

The project is set up so that almost everything happens automatically once it’s configured. Here’s the typical flow from development to deployment, highlighting the role of each component:

1.  **Development & Version Control:** A developer makes changes in the code – for example, improving the Poller’s data parsing or adding a new service. They commit and push the changes to the repository (on a specific branch or the main branch).
    
2.  **Continuous Integration (CI) with Jenkins:** Jenkins, which is connected to the repository, detects the commit (usually via a webhook or polling). The corresponding Jenkins pipeline for that component is triggered:
    
    -   Jenkins spins up a pod in Kubernetes to run the build (using the pod template that has Python and AWS tools ready).
        
    -   The pipeline (as defined in the Jenkinsfile) executes. For example:
        
        -   **If it’s a Lambda service (Poller/InfluxWriter):** Jenkins installs dependencies, packages the code into a ZIP, and uploads it to S3 or directly updates the Lambda code. Then it runs the Terraform (OpenTofu) step to ensure the AWS infrastructure (Lambda function configuration, etc.) is up to date[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/influx-writer/Jenkinsfile). This might create a new Lambda or update settings like environment variables if they changed. The Poller Jenkinsfile also calculates a hash of the new code and passes it to Terraform to force Lambda code update if needed[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/poller/Jenkinsfile).
            
        -   **If it’s a containerized service (e.g., ingest):** Jenkins builds the Docker image using the service’s Dockerfile. It then logs in to GHCR (using stored credentials) and pushes the new image with an appropriate tag (often “latest” or a git commit SHA). Optionally, Jenkins could update the Kubernetes manifest (in `deployments/`) with a new image tag or digest – but in our setup we usually use the `:latest` tag for simplicity, so updating the image in the registry is enough.
            
    -   Jenkins reports success or failure. If something fails (tests don’t pass or deployment issues), Jenkins will mark the build as failed, and no changes are applied to production in that case.
        
3.  **Continuous Deployment (CD) with ArgoCD:** For changes that involve Kubernetes manifests (or new images):
    
    -   If a manifest file was updated (e.g., you edited a Deployment yaml or added a new service manifest), ArgoCD notices the git change. It will automatically sync the changes to the cluster. For instance, if you increased a replica count or changed an environment variable in the manifest, ArgoCD applies that change using kubectl under the hood.
        
    -   If only the image was updated (say a new `latest` image is pushed) but the manifest wasn’t changed, Kubernetes will not automatically pull the new image unless a redeploy is triggered. In practice, you might update the Deployment’s image tag (e.g., use a version tag or update an image digest) to let ArgoCD deploy the new version. Alternatively, one can manually instruct the cluster to fetch the latest or restart the pod. In a more advanced setup, an automated image update controller could detect new images and update the manifests.
        
    -   Assuming the manifest is in sync, ArgoCD ensures the new or changed service is running. For example, if a new microservice was added in git, ArgoCD will create that Deployment and Service on the cluster. If an image tag changed, it will perform a rolling update of the pods.
        
4.  **Infrastructure Changes:** If the commit included changes to Terraform files (in `infrastructure/opentofu`) or Ansible playbooks (in `infrastructure/ansible`):
    
    -   Those typically would be applied through a Jenkins pipeline as well (perhaps a dedicated infrastructure pipeline or a manual trigger). For instance, if we alter the Terraform configuration to allocate more AWS resources or open a new port, we can run Jenkins to apply those changes. The state is stored (Terraform state, possibly in a backend or locally in the repo) to keep track of cloud resources.
        
    -   Ansible changes (like modifying how Grafana is configured) might be applied by re-running the ansible playbook on the VM. This could be initiated through Jenkins or run manually via an SSH connection, depending on how it’s set up. In a fully automated pipeline, one could have Jenkins SSH into the VM and run the Ansible playbook, or use a tool like Ansible AWX.
        
5.  **Monitoring & Feedback:** Once deployed, all parts of the system are monitored:
    
    -   The Lambdas can be monitored via CloudWatch (for invocations, errors).
        
    -   The Kubernetes cluster components (Jenkins, Grafana, etc.) are monitored by Prometheus. If something crashes, Kubernetes will try to restart it, and we can see metrics/dashboards for performance.
        
    -   Grafana provides a live view of the seismic data coming in. If the Poller is running correctly, you should see data points appearing on Grafana’s dashboard (e.g., points on a graph for each earthquake event).
        
    -   Developers or users can check Grafana to verify that data is flowing (heartbeats from Poller, events recorded). The Poller sends a heartbeat to InfluxDB each run[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/poller/src/handler.py), so that could be visualized as a simple uptime metric for the data pipeline.
        
6.  **User Interaction:** End-users (or project maintainers) mostly interact with the system via Grafana dashboards or any alert notifications:
    
    -   Grafana allows creating alerts as well (e.g., if a certain magnitude threshold is crossed, Grafana/Prometheus could trigger an alert). In the future, the Notifier service will likely handle such alerts more directly.
        
    -   If needed, a user can also query the InfluxDB database (using InfluxQL or Flux queries via the InfluxDB UI or CLI) to get raw data for analysis.
        

The beauty of this flow is that after the initial setup, **most operations are hands-off**. Pushing code triggers builds and deployments, and git is the single source of truth for both application code and deployment config. If something needs to be rolled back, you can revert the commit and ArgoCD will roll back the deployment, or Jenkins can re-deploy an older image if needed. This setup reduces the chance of configuration drift and makes it easier for multiple developers to collaborate (everyone can see changes in the repo history).

## Usage and Instructions

For developers and users of the Seismicity platform, here are some tips to get started and interact with the system:

-   **Accessing Grafana (Dashboards):** Grafana is the primary interface for viewing seismic data. After deployment, Grafana is available at the Azure VM’s public address. For example, if you have the DNS or IP (say `seismicity.westeurope.cloudapp.azure.com`), you can access Grafana on port 32002 (e.g., `http://seismicity.westeurope.cloudapp.azure.com:32002`). Upon first access, you’ll need to log in (the default Grafana credentials are often `admin/admin` unless changed by the Ansible setup – the Ansible roles might have set a default password or you can configure it via the Helm values).
    
    -   Once logged in, you should find a pre-configured **“Seismicity Dashboard”** or similar, which visualizes the data from InfluxDB. This dashboard could include graphs of earthquake magnitudes over time, counts of events per hour/day, and possibly geographical maps if configured. There is also likely a dashboard for **Kubernetes cluster monitoring** (since a ConfigMap for a “k8s cluster” dashboard was created[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/ansible/roles/grafana/tasks/main.yaml)). This can show you the health of the cluster and Jenkins.
        
    -   Feel free to interact with the Grafana panels: you can zoom in on time ranges, set up alerts, or even create new panels/queries using the InfluxDB data source. The data source should be pre-configured (the Ansible template sets up Grafana with the InfluxDB URL and access token).
        
-   **Viewing Jenkins (CI/CD):** Jenkins is running on the cluster and exposed on port 32000. You can visit `http://seismicity.westeurope.cloudapp.azure.com:32000` (or the VM’s IP with `:32000`) to access the Jenkins UI. You will need the Jenkins credentials (these were set during deployment; Ansible uses an existing secret for Jenkins credentials[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/ansible/roles/jenkins/tasks/main.yaml), so ask the maintainer or check the vault/secret if you have access). Once logged in:
    
    -   You can view the pipelines for each service. The monorepo likely uses multibranch pipelines or individual jobs for each Jenkinsfile. For example, there might be jobs named “Poller”, “Influx Writer”, “Ingest”, etc.
        
    -   You can trigger builds manually by running a job, or configure webhooks so that pushes to specific branches auto-start builds.
        
    -   Jenkins will show console logs for each stage of the pipeline (useful for debugging if a build or deployment fails).
        
    -   The Jenkins UI also allows managing credentials (like AWS keys, GHCR tokens, etc.) which are used in pipelines. These were set up initially (for example, an `aws-credentials` entry and `influxdb-token` were configured for pipeline use[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/influx-writer/Jenkinsfile)).
        
-   **Updating a Service:** To update or fix a microservice:
    
    -   Make your code changes in the relevant `services/<name>` directory. Update the code or add dependencies to `requirements.txt` as needed.
        
    -   If you add new files, ensure the Dockerfile or packaging script includes them. For example, if the service is a Lambda, make sure the Jenkinsfile’s packaging step includes that file. If it’s a Docker service, ensure the Dockerfile copies that file.
        
    -   Commit and push your changes to the repository.
        
    -   Go to Jenkins and run the pipeline for that service (if not automated). Watch the output to ensure the build and deploy steps succeed.
        
    -   Once Jenkins finishes, verify the deployment:
        
        -   For Lambdas, you can check AWS Lambda console to see if the function code was updated (and CloudWatch logs for it running).
            
        -   For Kubernetes services, ArgoCD’s UI (if set up) or CLI can show if the application is synced. You can also use `kubectl` (by logging into the VM or if you have the Kubeconfig) to check that the pods are updated (`kubectl get pods -n <namespace>`).
            
        -   Check Grafana to see if data is still flowing or if your change had the intended effect.
            
-   **Running Locally (Development):** If you want to simulate parts of the system locally:
    
    -   A `docker-compose.yml` is provided for the ingest-processor-notifier pipeline[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/docker-compose.yml). You can run `docker-compose up --build` from the repository root to start the ingest, processor, and notifier services locally. They will be built from the local Dockerfiles. Right now these just print messages (since they are placeholders), but this can be useful for development when implementing their logic. You can add functionality and quickly test it with Docker Compose before pushing.
        
    -   For the Lambdas (Poller and InfluxWriter), you can run them locally by simulating events:
        
        -   Poller can be run as a simple Python script (the `handler.py` has a `handler(event, context)` function – you could call it manually or adapt it to run on a schedule locally). You’ll need to set environment variables like `INFLUX_URL`, `INFLUX_TOKEN`, etc., for it to work outside AWS.
            
        -   InfluxWriter’s function `handler(event, context)` can be invoked with a sample event JSON to test writing to a local or test InfluxDB instance.
            
        -   It might be easier to test these in AWS directly, but local testing can be done with the right environment setup.
            
    -   If you make significant changes, remember to also update or create tests (if following best practices) and run them. The CI pipeline could be extended to run unit tests as part of the Jenkins process.
        
-   **Dashboard Customization:** Grafana is already set up, but you might want to tailor the dashboards:
    
    -   You can add graphs for different time ranges, or create alerts (Grafana can send alerts via email, Slack, etc., if configured with an alert channel).
        
    -   For example, you could add a panel that shows the number of earthquakes above a certain magnitude in the last 24 hours. Or a table listing recent events with time, location, magnitude, depth.
        
    -   Changes you make in Grafana’s UI can be saved. If you want to version-control dashboards, consider exporting them to JSON and adding them to the repository (the project already adds a Grafana dashboard JSON to a ConfigMap via Ansible[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/ansible/roles/grafana/tasks/main.yaml)).
        
-   **Notifications (Future):** While the Notifier service is not yet implemented, you can simulate what it might do:
    
    -   Possibly integrate with a service like AWS SNS, Twilio, or email SMTP to send messages.
        
    -   This would involve adding credentials securely (likely via Kubernetes secrets or Jenkins credentials) and writing the logic in the notifier’s code to trigger on certain conditions (like an earthquake above magnitude 5.0).
        
    -   Keep an eye on the repository’s updates or issues for plans on the Notifier implementation if you’re interested in contributing.
        

**Tip:** Since this is a monorepo with many moving parts, a good practice is to update one component at a time and verify the system’s overall functionality. For instance, if you update the Poller, check that data still flows to InfluxDB and appears in Grafana. If you update infrastructure (Terraform/Ansible), check that all services (Jenkins, Grafana, etc.) are still reachable and working after applying changes.

## Conclusion and Next Steps

The Seismicity project is a work in progress that already covers a wide range of technologies. It provides a foundation that can be expanded in numerous ways:

-   **Feature enhancements:** Implementing the Processor and Notifier logic to complete the in-cluster processing pipeline, adding more data sources (maybe other seismic APIs or local sensor inputs), or enabling geospatial visualizations in Grafana.
    
-   **Scaling and Hardening:** Moving from MicroK8s to a multi-node Kubernetes cluster or a managed service (like AKS or EKS) for greater reliability, implementing better error handling and retries in Lambdas, and adding security measures (RBAC in Kubernetes, secret management through Vault or AWS Secrets Manager, etc.).
    
-   **User Interface:** Perhaps integrating a web frontend or maps to display earthquake data on a map in real-time (Grafana has some plugins for maps, or a custom web app could use the data from InfluxDB).
    
-   **Alerts and Notifications:** Finalizing the notifier to deliver timely alerts to users who need them.