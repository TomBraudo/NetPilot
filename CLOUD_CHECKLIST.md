# NetPilot Google Cloud Deployment Checklist

> Complete setup guide for deploying NetPilot to Google Cloud Platform
> Optimized for cost-effectiveness while maintaining reliability

---

## 🎯 Overview

This checklist covers all Google Cloud services needed to deploy NetPilot with:
- **Backend**: Flask API in Docker container
- **Frontend**: React SPA served via Nginx
- **Connectivity**: Reverse SSH tunnel to OpenWrt routers
- **Domain**: Custom domain with SSL
- **Monitoring**: Basic observability and backups

**Estimated Monthly Cost**: $15-25 USD (e2-micro instance + minimal storage)

---

## ✅ Service Checklist

### 1. Google Cloud Project Setup
- [ ] **Create GCP Project**
- [ ] **Enable Required APIs**
- [ ] **Set up Billing**
- [ ] **Configure IAM & Service Accounts**

### 2. Compute Engine (VM)
- [ ] **Create VM Instance**
- [ ] **Configure Firewall Rules**
- [ ] **Set up SSH Access**

### 3. Container Registry/Artifact Registry
- [ ] **Enable Artifact Registry**
- [ ] **Create Docker Repository**
- [ ] **Configure Docker Authentication**

### 4. Cloud DNS (Optional)
- [ ] **Set up DNS Zone**
- [ ] **Configure Domain Records**

### 5. Cloud Storage
- [ ] **Create Storage Bucket**
- [ ] **Configure Backup Storage**

### 6. Cloud Monitoring
- [ ] **Enable Monitoring**
- [ ] **Set up Uptime Checks**
- [ ] **Configure Alerts**

### 7. Security & SSL
- [ ] **Configure Let's Encrypt**
- [ ] **Set up Firewall Rules**

---

## 📋 Detailed Setup Instructions

### 1. Google Cloud Project Setup

#### 1.1 Create GCP Project
```bash
# Using gcloud CLI (install from https://cloud.google.com/sdk/docs/install)
gcloud auth login
gcloud projects create netpilot-prod --name="NetPilot Production"
gcloud config set project netpilot-prod
```

**Manual Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name: `NetPilot Production`
4. Project ID: `netpilot-prod` (or auto-generated)
5. Click "Create"

#### 1.2 Enable Required APIs
```bash
gcloud services enable compute.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable dns.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable storage.googleapis.com
```

**Manual Steps:**
1. Go to "APIs & Services" → "Library"
2. Search and enable:
   - Compute Engine API
   - Artifact Registry API
   - Cloud DNS API (if using GCP DNS)
   - Cloud Monitoring API
   - Cloud Storage API

#### 1.3 Set up Billing
1. Go to "Billing" in the console
2. Link a billing account
3. Set up billing alerts:
   - Budget: $30/month
   - Alert at 50%, 90%, 100%

#### 1.4 Configure Service Account
```bash
# Create service account for the application
gcloud iam service-accounts create netpilot-app \
    --description="NetPilot application service account" \
    --display-name="NetPilot App"

# Grant necessary roles
gcloud projects add-iam-policy-binding netpilot-prod \
    --member="serviceAccount:netpilot-app@netpilot-prod.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create ~/netpilot-sa-key.json \
    --iam-account=netpilot-app@netpilot-prod.iam.gserviceaccount.com
```

---

### 2. Compute Engine (VM)

#### 2.1 Create VM Instance

**Recommended Specs (Cost-Optimized):**
- **Machine Type**: `e2-micro` (0.25-2 vCPUs, 1 GB RAM)
- **Boot Disk**: 20 GB Standard persistent disk
- **Region**: Choose closest to your users (e.g., `us-central1-a`)
- **OS**: Ubuntu 22.04 LTS

```bash
gcloud compute instances create netpilot-vm \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=netpilot-app@netpilot-prod.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=netpilot-vm,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20240319,mode=rw,size=20,type=projects/netpilot-prod/zones/us-central1-a/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,project=netpilot \
    --reservation-affinity=any
```

**Manual Steps:**
1. Go to "Compute Engine" → "VM instances"
2. Click "Create Instance"
3. Configure:
   - **Name**: `netpilot-vm`
   - **Region**: `us-central1` (Iowa)
   - **Zone**: `us-central1-a`
   - **Machine configuration**: 
     - Series: `E2`
     - Machine type: `e2-micro` (1 vCPU, 1 GB memory)
   - **Boot disk**: 
     - Operating system: `Ubuntu`
     - Version: `Ubuntu 22.04 LTS`
     - Size: `20 GB`
     - Disk type: `Standard persistent disk`
   - **Firewall**: Allow HTTP and HTTPS traffic
4. Click "Create"

#### 2.2 Configure Firewall Rules
```bash
# Allow SSH, HTTP, HTTPS, and custom SSH tunnel port
gcloud compute firewall-rules create netpilot-allow-web \
    --allow=tcp:22,tcp:80,tcp:443,tcp:2200 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow web traffic and SSH tunnel for NetPilot"

# More restrictive SSH access (optional)
gcloud compute firewall-rules create netpilot-allow-ssh-restricted \
    --allow=tcp:22 \
    --source-ranges=YOUR_IP_ADDRESS/32 \
    --target-tags=netpilot-ssh \
    --description="Restricted SSH access for NetPilot"
```

#### 2.3 Set up SSH Access
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/netpilot-gcp

# Add SSH key to VM
gcloud compute ssh netpilot-vm --zone=us-central1-a --ssh-key-file=~/.ssh/netpilot-gcp
```

---

### 3. Artifact Registry (Docker Images)

#### 3.1 Enable and Create Repository
```bash
# Create Docker repository
gcloud artifacts repositories create netpilot-docker \
    --repository-format=docker \
    --location=us-central1 \
    --description="NetPilot Docker images"
```

#### 3.2 Configure Docker Authentication
```bash
# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Test access
docker pull hello-world
docker tag hello-world us-central1-docker.pkg.dev/netpilot-prod/netpilot-docker/hello-world
docker push us-central1-docker.pkg.dev/netpilot-prod/netpilot-docker/hello-world
```

---

### 4. Cloud DNS (Optional - if not using external provider)

#### 4.1 Set up DNS Zone
```bash
# Create DNS zone for your domain
gcloud dns managed-zones create netpilot-zone \
    --description="NetPilot DNS zone" \
    --dns-name=yourdomain.com \
    --visibility=public
```

#### 4.2 Configure Domain Records
```bash
# Get name servers
gcloud dns managed-zones describe netpilot-zone

# Add A record pointing to your VM
gcloud compute instances describe netpilot-vm --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

# Create A record
gcloud dns record-sets create yourdomain.com \
    --zone=netpilot-zone \
    --type=A \
    --ttl=300 \
    --rrdatas=VM_EXTERNAL_IP
```

---

### 5. Cloud Storage (Backups)

#### 5.1 Create Storage Bucket
```bash
# Create bucket for backups
gcloud storage buckets create gs://netpilot-backups-$(date +%s) \
    --location=us-central1 \
    --storage-class=STANDARD
```

#### 5.2 Configure Lifecycle Policy
Create `lifecycle.json`:
```json
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 30}
    }
  ]
}
```

```bash
gcloud storage buckets update gs://netpilot-backups-XXXXX --lifecycle-file=lifecycle.json
```

---

### 6. Cloud Monitoring

#### 6.1 Enable Monitoring
```bash
# Monitoring is enabled by default, but verify
gcloud services enable monitoring.googleapis.com
```

#### 6.2 Set up Uptime Checks
**Manual Steps:**
1. Go to "Monitoring" → "Uptime checks"
2. Click "Create Uptime Check"
3. Configure:
   - **Title**: `NetPilot Health Check`
   - **Check Type**: `HTTP`
   - **Resource Type**: `URL`
   - **Hostname**: `yourdomain.com`
   - **Path**: `/api/health`
   - **Check frequency**: `5 minutes`
4. Click "Create"

#### 6.3 Configure Alerts
1. Go to "Monitoring" → "Alerting"
2. Create policies for:
   - VM CPU usage > 80%
   - VM memory usage > 90%
   - Uptime check failures
   - Disk usage > 85%

---

### 7. VM Initial Setup

#### 7.1 Connect to VM and Install Dependencies
```bash
# SSH into the VM
gcloud compute ssh netpilot-vm --zone=us-central1-a

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Create application user
sudo useradd -m -s /bin/bash netpilot
sudo usermod -aG docker netpilot

# Create application directories
sudo mkdir -p /opt/netpilot/{data,logs}
sudo chown -R netpilot:netpilot /opt/netpilot

# Install other dependencies
sudo apt install -y git curl wget unzip
```

#### 7.2 Configure Firewall (UFW)
```bash
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 2200/tcp  # SSH tunnel port
sudo ufw status
```

#### 7.3 Set up SSL with Let's Encrypt
```bash
# Install certbot
sudo apt install snapd
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# After deploying your app with domain pointing to the VM:
sudo certbot --nginx -d yourdomain.com
```

---

## 💰 Cost Optimization Tips

### 1. VM Optimization
- **Use e2-micro**: Free tier eligible (if within limits)
- **Use preemptible instances**: 60-91% cost savings (for non-critical workloads)
- **Auto-shutdown**: Schedule VM to stop during low-usage hours

### 2. Storage Optimization
- **Use Standard persistent disk**: Cheaper than SSD for small workloads
- **Enable automatic snapshots**: Cost-effective backup strategy
- **Set retention policies**: Automatically delete old backups

### 3. Network Optimization
- **Use regional resources**: Avoid cross-region charges
- **Monitor egress**: Most ingress is free, egress is charged

### 4. Monitoring
```bash
# Set up budget alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT_ID \
    --display-name="NetPilot Budget" \
    --budget-amount=30USD \
    --threshold-rules-percent=0.5,0.9,1.0
```

---

## 🔧 Next Steps After Cloud Setup

1. **Deploy Application**: Follow Phase 2-3 of IMPLEMENTATION_PLAN.md
2. **Configure Reverse SSH**: Set up tunnel from OpenWrt router
3. **Test End-to-End**: Verify full functionality
4. **Set up CI/CD**: Automate deployments
5. **Monitor & Optimize**: Watch costs and performance

---

## 📚 Useful Commands

```bash
# Check VM status
gcloud compute instances list

# Check costs
gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT_ID

# View logs
gcloud logging read "resource.type=gce_instance"

# SSH to VM
gcloud compute ssh netpilot-vm --zone=us-central1-a

# Stop VM (cost saving)
gcloud compute instances stop netpilot-vm --zone=us-central1-a

# Start VM
gcloud compute instances start netpilot-vm --zone=us-central1-a
```

---

**Total Estimated Setup Time**: 2-3 hours
**Monthly Cost**: $15-25 USD (depending on usage)

Ready to deploy NetPilot to the cloud! 🚀 