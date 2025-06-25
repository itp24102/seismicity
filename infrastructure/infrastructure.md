## `seismicity/infrastructure/` 

This directory contains the Infrastructure-as-Code and automation scripts that provision and configure the underlying platform across cloud providers. It is divided into two main parts: **OpenTofu (Terraform)** configurations for cloud resource provisioning, and **Ansible** playbooks for post-provisioning setup on servers.

-   **OpenTofu Provisioning:** The project uses **OpenTofu** (an open-source Terraform variant) to create and manage cloud resources on providers like AWS and Azure. The Terraform code is organized into subdirectories under `opentofu/` for each environment:
    
    -   **AWS:** Terraform code to deploy AWS resources, including AWS Lambda functions and their prerequisites. For example, there are configurations for the **Poller** and **Influx Writer** Lambdas. The AWS config provisions an S3 bucket (for storing data and code packages) and two Lambda functions: one for polling seismic data and one for writing to InfluxDB[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/aws/main.tf)[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/aws/main.tf). It also references existing AWS IAM roles for the Lambdas to run with proper permissions.
        
    -   **Azure:** Terraform code to set up an Azure environment to host our Kubernetes cluster. It creates resources like a Resource Group, Virtual Network, Subnet, Security Group, and a Virtual Machine[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/azure/main.tf). The VM (an Ubuntu Linux instance) is where **MicroK8s** (a lightweight Kubernetes) will run. The Security Group is configured to allow necessary inbound ports (SSH, HTTP/HTTPS, and NodePorts for services) – for example, ports 32000 (Jenkins), 32001 (Prometheus), and 32002 (Grafana) are opened for external access[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/azure/main.tf)[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/opentofu/azure/main.tf).
        
    -   **Structure:** The `opentofu` folder contains separate sub-folders for different components. For instance, `aws/poller` and `aws/influx-writer` contain Terraform modules specific to those Lambda functions (including their code deployment settings), while the `azure/` folder contains the main Azure infrastructure module. This separation makes it easy to manage or apply changes to one cloud environment without affecting the other.
        
-   **Ansible Configuration:** After cloud resources are provisioned, **Ansible** playbooks in this directory automate the configuration of the Azure VM and the Kubernetes cluster:
    
    -   The Ansible playbook (e.g. `ansible/site.yaml`) targets the new VM (grouped as “servers”) to perform post-provisioning steps. It installs and configures **MicroK8s** (turning the VM into a single-node Kubernetes cluster) along with necessary tools like Docker if needed.
        
    -   **Kubernetes Add-ons via Helm:** Once MicroK8s is running, Ansible uses Helm charts to deploy essential services into the cluster:
        
        -   **Jenkins:** Deploys a Jenkins server on MicroK8s using the official Helm chart, exposed as a NodePort (32000) for external access[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/ansible/roles/jenkins/tasks/main.yaml). Jenkins is used for CI/CD (see below).
            
        -   **Prometheus & Grafana:** Installs monitoring components. Prometheus (via the kube-prometheus-stack) is set up, and Grafana is installed with a default data source and dashboard. Grafana is exposed on NodePort 32002[GitHub](https://github.com/itp24102/seismicity/blob/a42ff8cd8d24b42479b0c630206af062429aa819/infrastructure/ansible/roles/grafana/tasks/main.yaml). The Ansible roles configure Grafana with an InfluxDB data source and even pre-load a dashboard (via a ConfigMap) for visualizing cluster or seismic data.
            
        -   **InfluxDB:** Sets up InfluxDB for time-series data storage. InfluxDB may be installed on the host or within MicroK8s (in this project it’s configured to be accessible at port 8086 on the VM). Ansible ensures InfluxDB is running and ready to receive data (the **Influx Writer** Lambda will write to this database).
            
    -   **System Configuration:** Ansible can also handle general system setup like applying OS updates, configuring Docker, and other system settings on the VM as needed for the services above.
        
-   **Subdirectory Layout:** In summary, `infrastructure/opentofu/` contains Terraform config files (grouped by cloud and service), and `infrastructure/ansible/` contains:
    
    -   Ansible playbooks (like `site.yaml`) to orchestrate the roles.
        
    -   Ansible roles in `roles/` (e.g., roles for jenkins, grafana, prometheus, influxdb) each with tasks to install/configure that component.
        
    -   Template and file assets for configuration (for example, Grafana data source templates, dashboard JSON files, etc., used by the roles).
        

All these tools work together to automatically provision the needed cloud infrastructure and configure the Kubernetes environment. By running the Terraform (OpenTofu) and then Ansible playbooks, you can go from zero to a fully set-up platform: a VM with Kubernetes and monitoring tools, plus AWS Lambdas for data ingestion. This automation reduces manual setup and ensures consistency across environments.