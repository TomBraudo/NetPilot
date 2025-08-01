# NetPilot Backend2 Cloud Deployment Guide

## Overview

This guide provides step-by-step instructions to deploy the NetPilot Backend2 Flask application to **Google Cloud Run** and set up a CI/CD pipeline for automatic deployments on pushes/PRs to the `New-Main` branch.

Google Cloud Run is a fully managed serverless platform that automatically scales your containerized applications and charges only for the resources you use.

## Prerequisites

- Google Cloud Platform (GCP) account
- GitHub repository access
- Domain name (optional, can use Google Cloud Run's default URL)
- Database is already running at `34.38.207.87:5432`
- Commands server is already running at `34.38.207.87:5000`

## Google Cloud Run Deployment

### ✅ Step 1: Prepare the Application for Containerization (COMPLETED)

1. **Dockerfile** (Already created in backend2 directory):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --shell /bin/bash app
USER app
EXPOSE 8080
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
CMD ["python", "server.py"]
```

2. **.dockerignore** (Already created):

```
__pycache__/
*.pyc
venv/
.env.local
.env.production
.env
logs/
*.log
.git/
test_*.py
```

3. **Server.py is already updated** to use PORT environment variable for production deployment.

### ✅ Step 2: Set up Google Cloud Project (COMPLETED)

1. **Install Google Cloud CLI:**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Run: `gcloud init`
   - Select your project or create a new one

2. **Enable required APIs:**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

3. **Set up authentication:**
```bash
gcloud auth configure-docker
```

### ✅ Step 3: Set up Environment Variables with Secret Manager (COMPLETED)

For production deployments, we'll use Google Cloud Secret Manager to securely store sensitive environment variables.

1. **Enable Secret Manager API:**
```bash
gcloud services enable secretmanager.googleapis.com
```

2. **Create secrets for sensitive variables:**
```bash
# Create secrets for SENSITIVE data only

```

**Note:** URLs like `COMMAND_SERVER_URL` are not secrets - they'll be set as regular environment variables during deployment.

3. **Grant Cloud Run access to secrets:**
```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe net-pilot-463708 --format="value(projectNumber)")

# Grant the Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding google-client-secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding flask-secret-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding database-url \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 4: Deploy to Cloud Run with Secret Manager

1. **Deploy with Secret Manager integration:**
```bash
# First, clone the repository from New-Main branch (since you need the source code)
cd /tmp
git clone -b New-Main https://github.com/TomBraudo/NetPilot.git
cd NetPilot/backend2

# Deploy with ALL required environment variables
gcloud run deploy netpilot-backend2 \
    --source . \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars="GOOGLE_CLIENT_ID=1053980213438-p4jvv47k3gmcuce206m5iv8cht0gpqhu.apps.googleusercontent.com,COMMAND_SERVER_URL=http://34.38.207.87:5000,COMMAND_SERVER_TIMEOUT=30,DB_HOST=34.38.207.87,DB_PORT=5432,DB_USERNAME=netpilot_user,DB_NAME=netpilot_db,FLASK_ENV=production,DB_ECHO=false,LOG_LEVEL=INFO,PORT=8080" \
    --set-secrets="GOOGLE_CLIENT_SECRET=google-client-secret:latest,DB_PASSWORD=db-password:latest,SECRET_KEY=flask-secret-key:latest,DATABASE_URL=database-url:latest"
```

**Note:** Since `.env` is not committed to Git, all environment variables are explicitly set in the deployment command above.

**Important:** If you encounter psycopg2 build issues, first commit and push the updated requirements.txt and Dockerfile to your repository, then clone the latest version.

2. **Update CORS settings:**
After deployment, you'll get a URL like `https://netpilot-backend2-xxx-uc.a.run.app`

Update your `server.py` CORS configuration to include this URL:

```python
CORS(app, 
     origins=[
         'http://localhost:3000', 
         'http://localhost:5173', 
         'https://netpilot-backend2-xxx-uc.a.run.app'  # Replace with your actual URL
     ],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
```

## CI/CD Pipeline Setup with GitHub Actions

### Step 1: GitHub Actions Workflow

The workflow file has already been created at `.github/workflows/deploy-backend2.yml`. It automatically:

- Triggers on pushes to `New-Main` branch (only when backend2 files change)
- Triggers on merged pull requests to `New-Main` branch
- Builds and deploys to Google Cloud Run using Secret Manager
- Uses GitHub secrets for non-sensitive environment variables only

### Step 2: Set up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository Secrets**:

**Google Cloud Authentication:**
- `GCP_SA_KEY`: Service account JSON key (base64 encoded) - see Step 4 below
- `GCP_PROJECT_ID`: Your Google Cloud project ID

**Non-sensitive Application Environment Variables:**
- `GOOGLE_CLIENT_ID`: `1053980213438-p4jvv47k3gmcuce206m5iv8cht0gpqhu.apps.googleusercontent.com`
- `COMMANDS_SERVER_URL`: `http://34.38.207.87:5000`
- `DB_HOST`: `34.38.207.87`
- `DB_PORT`: `5432`
- `DB_USERNAME`: `netpilot_user`
- `DB_NAME`: `netpilot_db`

**Note:** Sensitive variables (passwords, secret keys) are stored in Google Cloud Secret Manager, not GitHub secrets.

### Step 3: Set Repository Variables

Go to your GitHub repository → Settings → Secrets and variables → Actions → Variables tab

Add this **Repository Variable**:
- `DEPLOYMENT_TYPE`: `cloudrun`

### Step 4: Create Google Cloud Service Account

1. **Create service account:**
```bash
# Replace YOUR_PROJECT_ID with your actual Google Cloud project ID
gcloud iam service-accounts create github-actions \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions"
```

2. **Grant necessary permissions:**
```bash
# Replace YOUR_PROJECT_ID with your actual project ID
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# If using Secret Manager, add additional permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"
```

3. **Create and download service account key:**
```bash
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. **Encode the key for GitHub:**
```bash
base64 github-actions-key.json
```

Copy the output and use it as the `GCP_SA_KEY` secret in GitHub.

## Managing Secret Manager

### Updating Secrets

To update any secret value:

```bash
# Update a secret (creates a new version)
echo -n "new_secret_value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Example: Update the database password
echo -n "new_secure_password" | gcloud secrets versions add db-password --data-file=-
```

### Viewing Secret Versions

```bash
# List all versions of a secret
gcloud secrets versions list SECRET_NAME

# View the latest version of a secret (for debugging)
gcloud secrets versions access latest --secret="SECRET_NAME"
```

### Adding New Secrets

```bash
# Create a new secret
echo -n "secret_value" | gcloud secrets create new-secret-name --data-file=-

# Grant Cloud Run access to the new secret
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding new-secret-name \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Update your deployment to use the new secret
gcloud run services update netpilot-backend2 \
    --region us-central1 \
    --set-secrets="NEW_ENV_VAR=new-secret-name:latest"
```

## Testing the Deployment

### Step 1: Manual Deployment Test

1. **Test locally first:**
```bash
cd backend2
python server.py
```

2. **Test Docker build locally:**
```bash
cd backend2
docker build -t netpilot-backend2 .
docker run -p 8080:8080 --env-file .env netpilot-backend2
```

3. **Manual Cloud Run deployment:**
Follow Step 4 from the deployment section above.

### Step 2: Test CI/CD Pipeline

1. **Make a small change to backend2:**
```bash
# Edit a comment in server.py or add a print statement
git add backend2/
git commit -m "Test deployment pipeline"
git push origin New-Main
```

2. **Monitor the deployment:**
- Go to GitHub → Actions tab
- Watch the deployment workflow run
- Check the logs for any issues

3. **Verify deployment:**
- Visit your Cloud Run URL
- Test the `/health` endpoint
- Try logging in with Google OAuth

## Post-Deployment Steps

### 1. Update Google OAuth Settings

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add your production URL to "Authorized redirect URIs":
   - `https://your-cloud-run-url.run.app/authorize`
5. Add your production URL to "Authorized JavaScript origins":
   - `https://your-cloud-run-url.run.app`

### 2. Test the Deployment

1. **Health Check:**
   ```bash
   curl https://your-cloud-run-url.run.app/health
   ```

2. **Test Authentication:**
   Visit your deployed URL and try logging in with Google

3. **Test API Endpoints:**
   ```bash
   # Test whitelist endpoint (requires authentication)
   curl -X GET "https://your-cloud-run-url.run.app/api/whitelist" \
        -H "Cookie: session=your-session-cookie"
   ```

### 3. Monitor Logs

**View Cloud Run logs:**
```bash
gcloud logs tail --follow --format="value(textPayload)" \
  --filter="resource.type=cloud_run_revision AND resource.labels.service_name=netpilot-backend2"
```

**View logs in Google Cloud Console:**
1. Go to Google Cloud Console
2. Navigate to Cloud Run → netpilot-backend2
3. Click on "Logs" tab

## Troubleshooting

### Common Issues

1. **Database Connection Issues:**
   - Verify the database server allows connections from Cloud Run (0.0.0.0/0 or specific Cloud Run IPs)
   - Check if firewall rules allow traffic on port 5432
   - Test connection: `gcloud cloud-shell ssh` then `nc -zv 34.38.207.87 5432`

2. **CORS Issues:**
   - Update CORS origins in `server.py` to include your production URL
   - Ensure the frontend is using the correct backend URL
   - Check browser developer tools for CORS errors

3. **Authentication Issues:**
   - Verify Google OAuth redirect URIs are correctly configured
   - Check that session cookies are working
   - Test OAuth flow manually

4. **Environment Variables:**
   - Ensure all required environment variables are set in Cloud Run
   - Check for typos in variable names
   - Use `gcloud run services describe netpilot-backend2 --region us-central1` to verify

5. **Build Issues:**
   - Check that all dependencies are in requirements.txt
   - Verify Dockerfile syntax
   - Test Docker build locally before deploying

### Debugging Commands

**View service details:**
```bash
gcloud run services describe netpilot-backend2 --region us-central1
```

**View recent deployments:**
```bash
gcloud run revisions list --service netpilot-backend2 --region us-central1
```

**Test external service connectivity:**
```bash
# Test from Cloud Shell
gcloud cloud-shell ssh
curl -v http://34.38.207.87:5000/api
nc -zv 34.38.207.87 5432
```

## Security Considerations

1. **HTTPS by default** - Cloud Run provides HTTPS automatically
2. **Update session cookie settings for production:**
   ```python
   app.config.update(
       SESSION_COOKIE_SECURE=True,  # Only send over HTTPS
       SESSION_COOKIE_HTTPONLY=True,  # Prevent XSS
       SESSION_COOKIE_SAMESITE='Strict',  # CSRF protection
   )
   ```
3. **Rotate secrets regularly** - Update GitHub secrets and redeploy
4. **Monitor for suspicious activities** using Cloud Logging

## Scaling and Performance

Cloud Run automatically handles scaling. You can configure:

**Set scaling parameters:**
```bash
gcloud run services update netpilot-backend2 \
    --region us-central1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 100 \
    --cpu 1 \
    --memory 512Mi \
    --timeout 300
```

## Quick Reference Commands

**Deploy:**
```bash
cd backend2
gcloud run deploy netpilot-backend2 --source . --region us-central1
```

**View logs:**
```bash
gcloud logs tail --follow --filter="resource.type=cloud_run_revision"
```

**Update environment variables:**
```bash
gcloud run services update netpilot-backend2 \
    --region us-central1 \
    --set-env-vars="NEW_VAR=value"
```

**Get service URL:**
```bash
gcloud run services describe netpilot-backend2 --region us-central1 --format="value(status.url)"
```

---

## Summary

Your backend2 server will now automatically deploy to Google Cloud Run whenever you push changes to the `New-Main` branch. The deployment is:

- ✅ **Containerized** and production-ready
- ✅ **Auto-scaling** based on traffic
- ✅ **Cost-effective** (pay only for usage)
- ✅ **Secure** with HTTPS by default
- ✅ **Integrated** with your existing database and commands server
- ✅ **Automated** via GitHub Actions CI/CD

Next steps: Set up your Google Cloud project, configure GitHub secrets, and push a test commit to see the magic happen!