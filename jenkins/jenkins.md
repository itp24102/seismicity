## `seismicity/jenkins/` 

The Jenkins directory contains configuration and supporting files for the project’s Continuous Integration/Continuous Deployment (CI/CD) pipelines. Jenkins is the engine that builds the code, container images, and deploys our services to their respective environments (AWS or Kubernetes).

-   **CI Pipelines:** Each microservice in the repository has a corresponding **Jenkinsfile** (usually located with the service code) that defines its build and deployment steps. Jenkins (running on our MicroK8s cluster) uses these pipelines to automate tasks like:
    
    -   Installing dependencies and running tests (if any) for the service.
        
    -   **Building Docker images** for services that run in containers (e.g., the `ingest`, `processor`, `notifier` services). Jenkins will build the Dockerfile and push the image to the GitHub Container Registry (GHCR) under our repository’s name. For example, the Kubernetes manifests refer to images like `ghcr.io/itp24102/ingest:latest`[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/deployments/ingest/deployment.yaml).
        
    -   **Packaging and uploading AWS Lambdas** for services that run as serverless functions (the **Poller** and **Influx Writer**). Jenkinsfile for those will zip the function code and upload it to AWS (often to an S3 bucket, then update the Lambda). In our case, Jenkins also triggers OpenTofu to apply any infrastructure changes for those Lambdas[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/influx-writer/Jenkinsfile), ensuring that if a new function or configuration change is needed, it’s handled automatically by infrastructure code.
        
    -   **Deploying to environments:** After building, Jenkins pipelines deploy changes. For Lambdas, this means updating the function code in AWS (and applying Terraform). For Kubernetes services, this means pushing a new container image (ArgoCD will pick up the change if the manifest is updated or uses the `latest` tag).
        
-   **Jenkins in Kubernetes:** The Jenkins server itself runs in the cluster (installed via Helm by Ansible). It uses the Kubernetes plugin to spawn ephemeral pods as build agents. The `jenkins/pod.yaml` file defines a custom pod template for Jenkins agents[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/jenkins/pod.yaml). This includes:
    
    -   A **Python container** (from `python:3.10-slim`) for running general build steps or scripts.
        
    -   An **AWS CLI + OpenTofu container** (our custom image `awscli-tofu:latest` from GHCR) for any steps that need AWS tools or Terraform. This image has AWS CLI, `curl`, `unzip`, and can run `tofu` (Terraform) commands[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/jenkins/influx-writer.Dockerfile), which our pipelines use to deploy infrastructure.
        
    -   The standard **Jenkins JNLP container** to connect the agent to the Jenkins master.  
        Using Kubernetes for build agents means our CI tasks are isolated in containers and can scale or clean up easily.
        
-   **Files in this Directory:** Aside from `pod.yaml`, this directory includes Dockerfiles and possibly scripts that support the Jenkins pipelines:
    
    -   **Dockerfiles:** For example, `awscli-tofu.Dockerfile` defines how to build the custom agent image with AWS CLI and OpenTofu tools installed. This ensures the Jenkins agent has all needed commands (like `aws` and `tofu`) available during pipeline execution.
        
    -   There may be service-specific Dockerfiles here as well (e.g., we have an `influx-writer.Dockerfile` which might have been used to build a particular environment for that pipeline). Generally, each Jenkinsfile will reference either a standard container or a custom one from these Dockerfiles.
        
    -   **Jenkins Pipeline Library/Config:** (If present) Any groovy scripts or shared library code for Jenkins would reside here, though in this project it appears that each service uses its own pipeline script and the main Jenkins configuration is handled via the Helm chart and GUI.
        
-   **CI/CD Flow with Jenkins:** In practice, when you push a change to the repository:
    
    -   Jenkins detects the change (if set up with webhooks or a poll) and triggers the pipeline for the affected service.
        
    -   The pipeline uses the steps defined in the Jenkinsfile: for example, the Poller Jenkinsfile will create a deployment package, upload it to S3, and then run `tofu apply` to update the AWS Lambda[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/poller/Jenkinsfile). A container service’s Jenkinsfile would build the Docker image and push it to GHCR.
        
    -   By the end of the pipeline, the new version of the service is either running (for Lambdas) or available for deployment (as a new container image for K8s). If the Kubernetes manifest is configured to auto-update (or if a developer updates the image tag in the manifest), ArgoCD will deploy the new image to the cluster.
        

Jenkins thus ties together the codebase and the operational environment, automating everything from building artifacts to invoking Terraform and updating deployments. This ensures continuous delivery of changes in a reliable, repeatable way.