# 🏥 Microservice Health Monitoring System on Amazon EKS

An enterprise-grade, cloud-native **Health Monitoring System** deployed on **Amazon EKS** with automated **GitHub Actions CI/CD**, persistent **Amazon EBS storage**, **AWS Application Load Balancer (ALB)** ingress, and full observability using **kube-prometheus-stack (Prometheus & Grafana)**.

---

## 📐 Architecture Overview

```mermaid
flowchart TD
    subgraph Developer & CI/CD Pipeline
        DEV[Developer Push to main] -->|git push| GH[GitHub Repository]
        GH --> ACTIONS[GitHub Actions Workflow .github/workflows/deploy.yml]
        ACTIONS --> TEST[Stage 1: Application Unit Tests]
        TEST --> DOCKER[Stage 2: Build Docker Images SHA & latest]
        DOCKER --> ECR_PUSH[Stage 3: Push Images to Amazon ECR]
        ECR_PUSH --> EKS_AUTH[Stage 4: Authenticate to Amazon EKS]
        EKS_AUTH --> ROLLOUT[Stage 5: Zero-Downtime Rolling Update]
        ROLLOUT --> STATUS[Stage 6: Verify Rollout Status]
    end

    subgraph AWS Cloud Infrastructure (us-east-1)
        subgraph Amazon EKS Cluster: health-monitoring-cluster
            ALB[AWS Application Load Balancer] --> INGRESS[ALB Ingress target-type: ip]
            
            subgraph Namespace: health-monitoring
                INGRESS --> DASHBOARD[monitoring-dashboard 2 Replicas]
                INGRESS --> USER_SVC[user-service 2 Replicas]
                INGRESS --> PAY_SVC[payment-service 2 Replicas]
                INGRESS --> NOTIF_SVC[notification-service 2 Replicas]
                
                DASHBOARD --> DB[(PostgreSQL 15 Persistent EBS gp3)]
                DASHBOARD --> REDIS[(Redis 7 Cache)]
                DASHBOARD --> RABBIT[(RabbitMQ 3 AMQP & Management EBS gp3)]
            end

            subgraph Namespace: monitoring
                PROM[Prometheus Server] --> GRAFANA[Grafana Dashboards :3000]
                PROM --> OPERATOR[Prometheus Operator]
                PROM --> METRICS[kube-state-metrics & node-exporter]
            end
        end
    end
```

---

## 🚀 Tech Stack

| Category | Technology |
| :--- | :--- |
| **Cloud Provider** | Amazon Web Services (AWS) - `us-east-1` |
| **Container Orchestration** | Amazon EKS (Kubernetes 1.36) |
| **Container Registry** | Amazon ECR |
| **Load Balancing** | AWS Application Load Balancer (ALB Ingress) |
| **Storage Driver** | AWS EBS CSI Driver (`ebs.csi.eks.amazonaws.com`) |
| **Microservices** | Python 3.12, FastAPI, Starlette, Uvicorn |
| **Databases & Messaging** | PostgreSQL 15, Redis 7, RabbitMQ 3 |
| **CI/CD Platform** | GitHub Actions |
| **Observability & Metrics** | Prometheus Operator, Prometheus Server, Grafana, Alertmanager |

---

## 📁 Repository Structure

```text
Healthcheck-project/
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # Production GitHub Actions CI/CD Pipeline
│
├── health-monitoring-system/
│   ├── monitoring-dashboard/       # FastAPI Frontend & Health Probe Worker
│   ├── user-service/               # User Authentication & Management Service
│   ├── payment-service/            # Payment Processing Microservice
│   ├── notification-service/       # Notification Dispatch Microservice
│   └── docker-compose.yml          # Local Multi-Container Development Setup
│
├── k8s/
│   ├── namespace.yaml              # Application Namespace (health-monitoring)
│   ├── storageclass.yaml           # EBS gp3 StorageClass (ebs-sc)
│   ├── pdb.yaml                    # PodDisruptionBudgets (MinAvailable: 1)
│   ├── hpa.yaml                    # HorizontalPodAutoscalers (CPU target: 70%)
│   ├── prometheus-values.yaml      # Custom Values for kube-prometheus-stack
│   ├── postgres/                   # PostgreSQL Stateful Manifests & Secrets
│   ├── redis/                      # Redis Deployment & Service
│   ├── rabbitmq/                   # RabbitMQ Deployment & PVC
│   ├── monitoring-dashboard/       # Dashboard Deployment & ClusterIP Service
│   ├── user-service/               # User Service Deployment & ClusterIP Service
│   ├── payment-service/            # Payment Service Deployment & ClusterIP Service
│   ├── notification-service/       # Notification Service Deployment & ClusterIP Service
│   └── ingress/
│       └── ingress.yaml            # AWS ALB Ingress Manifest
│
└── README.md                       # Master Architecture & Operations Guide
```

---

## ⚙️ GitHub Actions CI/CD Pipeline Setup

To run automated deployments on push to `main` or `master`, configure the following **GitHub Secrets** under **Repository Settings -> Secrets and variables -> Actions**:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | IAM User Access Key | `AKIAXXXXXXXXXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY` | IAM User Secret Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS Region | `us-east-1` |
| `AWS_ACCOUNT_ID` | 12-digit AWS Account ID | `552823821096` |
| `EKS_CLUSTER_NAME` | EKS Cluster Name | `health-monitoring-cluster` |

---

## 📊 Accessing Observability & Monitoring

### 1. Grafana Dashboards
* **Port-Forward Command**:
  ```powershell
  kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
  ```
* **URL**: [http://localhost:3000](http://localhost:3000)
* **Username**: `admin`
* **Password**: `adminpassword123`

### 2. Prometheus Query Engine
* **Port-Forward Command**:
  ```powershell
  kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
  ```
* **URL**: [http://localhost:9090](http://localhost:9090)

---

## 🌐 Live Web Application Credentials

* **AWS ALB Load Balancer URL**:  
  [http://k8s-healthmo-healthmo-7c9f0e0a8e-357124943.us-east-1.elb.amazonaws.com/login](http://k8s-healthmo-healthmo-7c9f0e0a8e-357124943.us-east-1.elb.amazonaws.com/login)
* **Default Admin Account**:
  * **Email**: `admin@example.com`
  * **Password**: `Admin@123`

---

## 🛠️ Operations & Maintenance Guide

### Check Cluster Status
```powershell
# Application pods
kubectl get pods,pvc,svc -n health-monitoring

# Monitoring stack pods
kubectl get pods,pvc -n monitoring
```

### Emergency Rollback (`kubectl rollout undo`)
If a bad build needs to be reverted immediately without downtime:
```powershell
kubectl rollout undo deployment/monitoring-dashboard -n health-monitoring
kubectl rollout undo deployment/user-service -n health-monitoring
kubectl rollout undo deployment/payment-service -n health-monitoring
kubectl rollout undo deployment/notification-service -n health-monitoring
```

### View Live Logs
```powershell
kubectl logs -l app=monitoring-dashboard -n health-monitoring --tail=100 -f
```
