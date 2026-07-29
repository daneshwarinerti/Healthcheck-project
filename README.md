# 🏥 Production Health Monitoring System on Amazon EKS

A enterprise-grade, microservice-based Health Monitoring System running on **Amazon EKS**, containerized with **Docker**, stored in **Amazon ECR**, routed by **AWS Application Load Balancer (ALB)**, backed by **Amazon EBS Storage**, and monitored with **kube-prometheus-stack (Prometheus & Grafana)**.

---

## 🏗️ Architecture Overview Diagram

```mermaid
flowchart TD
    subgraph Developer Workflow
        DEV[Developer Push Code] -->|git push| GH[GitHub Repository]
    end

    subgraph GitHub Actions CI/CD Pipeline
        GH --> WORKFLOW[GitHub Actions Workflow .github/workflows/deploy.yml]
        WORKFLOW --> TEST[Stage 1: Unit & Integration Tests]
        TEST --> BUILD[Stage 2: Build Docker Images tagged with SHA & latest]
        BUILD --> ECR_PUSH[Stage 3: Authenticate & Push to Amazon ECR]
        ECR_PUSH --> EKS_AUTH[Stage 4: Authenticate to Amazon EKS]
        EKS_AUTH --> ROLLOUT[Stage 5: Perform Zero-Downtime Rolling Update]
        ROLLOUT --> VERIFY[Stage 6: Verify Deployment Rollout Status]
    end

    subgraph AWS Cloud Infrastructure (us-east-1)
        subgraph EKS Cluster: health-monitoring-cluster (Namespace: health-monitoring)
            ALB[AWS Application Load Balancer] --> INGRESS[ALB Ingress target-type: ip]
            INGRESS --> DASHBOARD[monitoring-dashboard 2 Replicas]
            INGRESS --> USER_SVC[user-service 2 Replicas]
            INGRESS --> PAY_SVC[payment-service 2 Replicas]
            INGRESS --> NOTIF_SVC[notification-service 2 Replicas]
            
            DASHBOARD --> DB[(PostgreSQL 15 Persistent EBS gp3)]
            DASHBOARD --> REDIS[(Redis 7 Cache)]
            DASHBOARD --> RABBIT[(RabbitMQ 3 Management Persistent EBS gp3)]
        end
        
        subgraph Monitoring Namespace (monitoring)
            PROM[Prometheus Server] --> GRAFANA[Grafana Dashboards :3000]
            PROM --> OPERATOR[Prometheus Operator]
            PROM --> EXPORTER[Node Exporter & kube-state-metrics]
        end
    end
```

---

## 🔑 GitHub Secrets Configuration

To enable automated CI/CD deployment, configure the following secrets in your GitHub Repository under **Settings -> Secrets and variables -> Actions**:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | AWS IAM User Access Key | `AKIAXXXXXXXXXXXXXXXX` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM User Secret Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS Target Region | `us-east-1` |
| `AWS_ACCOUNT_ID` | 12-digit AWS Account Number | `552823821096` |
| `EKS_CLUSTER_NAME` | Name of your EKS Cluster | `health-monitoring-cluster` |

---

## 🛡️ AWS IAM OIDC Federation Setup (Best Practice)

If using GitHub OIDC instead of static AWS Access Keys:

### 1. IAM Role Trust Policy (`github-oidc-trust-policy.json`)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::552823821096:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<YOUR_GITHUB_USERNAME>/Healthcheck-project:*"
        }
      }
    }
  ]
}
```

---

## 🔄 Emergency Rollback Procedure

If a deployed build encounters runtime issues, use `kubectl rollout undo` to instantly revert to the previous revision without downtime:

### Revert a Deployment to Previous Revision
```powershell
# Rollback monitoring-dashboard
kubectl rollout undo deployment/monitoring-dashboard -n health-monitoring

# Rollback backend services
kubectl rollout undo deployment/user-service -n health-monitoring
kubectl rollout undo deployment/payment-service -n health-monitoring
kubectl rollout undo deployment/notification-service -n health-monitoring
```

### View Deployment Revision History
```powershell
kubectl rollout history deployment/monitoring-dashboard -n health-monitoring
```

---

## 📊 Live Verification Commands

```powershell
# Check all microservices and databases
kubectl get pods -n health-monitoring
kubectl get pvc -n health-monitoring
kubectl get svc -n health-monitoring
kubectl get ingress -n health-monitoring

# Check monitoring stack
kubectl get pods -n monitoring
```
