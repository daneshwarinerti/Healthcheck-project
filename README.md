# 🏥 Microservice Health Monitoring System on Amazon EKS

An enterprise-grade, cloud-native **Health Monitoring System** deployed on **Amazon EKS** with automated **GitHub Actions CI/CD**, persistent **Amazon EBS storage**, **AWS Application Load Balancer (ALB)** ingress, and full observability using **kube-prometheus-stack (Prometheus & Grafana)**.


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
