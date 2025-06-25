## `seismicity/deployments/` 

This directory contains Kubernetes manifest files for the project’s microservices, which are managed through ArgoCD for GitOps-style deployment. The manifests define how services like **ingest**, **processor**, and **notifier** should run on the Kubernetes cluster. These YAML files include Kubernetes **Deployments** and **Services** for each microservice (e.g. container images from GitHub Container Registry (GHCR)[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/deployments/ingest/deployment.yaml)). ArgoCD continuously monitors this folder and automatically applies any changes to the cluster, ensuring the infrastructure is always in sync with the repository.

-   **Purpose:** Provide a declarative source of truth for deploying seismicity microservices on Kubernetes. ArgoCD watches these manifests and keeps the cluster up-to-date.
    
-   **Current Contents:** Manifests for `ingest`, `processor`, and `notifier` microservices (listed in the kustomization file[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/deployments/kustomization.yaml)). Each service has a basic Deployment and Service definition.
    
-   **Placeholders:** These manifests are largely **placeholders** for future development. The associated services currently have minimal implementation (for example, the ingest service simply runs an idle loop[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/services/ingest/src/main.py)). They are deployed by ArgoCD but not yet performing any real data processing.
    
-   **ArgoCD Deployment:** Even though ArgoCD deploys these services to the cluster, they are not actively used in production yet. This setup ensures that once these services are fully developed, they will be automatically deployed without additional manual steps.
    

> **Note:** A Kubernetes secret (`ghcr-secret`) is referenced for pulling images from GHCR[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/deployments/ingest/deployment.yaml). Make sure to configure this secret in the cluster so that ArgoCD can pull the container images.