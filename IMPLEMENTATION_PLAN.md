# NetPilot Cloud Migration – IMPLEMENTATION PLAN

> Method 3 – Web-based SSH Gateway (Cloud-hosted backend & reverse SSH tunnel)
>
> This plan is tailored to the current NetPilot codebase (Flask + React).  Treat every **[ ]** item as an atomic task that can be checked off in a PR.

---

## Phase 0 – Preparation & Repository Hygiene

### 0.1  Baseline Audit
- [ ] Verify that `backend/server.py` starts locally and all endpoints respond (manual curl / Postman)
- [ ] Run the React dev server (`frontend/dashboard`) and confirm UI loads with local backend
- [ ] Freeze current requirements: `pip freeze > backend/requirements.lock`

### 0.2  Repo Structure & Branching
- [ ] Create long-lived branch `feature/cloud-migration`
- [ ] Add **CODEOWNERS** & PR template for consistent reviews

### 0.3  Issue Tracking
- [ ] Break down this PLAN into GitHub issues/milestones

---

## Phase 1 – Cloud Infrastructure

### 1.1  VM Provisioning
- [ ] Choose provider & region (DigitalOcean / Lightsail / EC2)
- [ ] Generate SSH key-pair locally and upload the public key
- [ ] Launch Ubuntu 22.04 LTS (≥1 vCPU, 2 GB RAM)

### 1.2  OS Hardening & Firewall
- [ ] `sudo apt update && sudo apt upgrade -y`
- [ ] Create non-root sudo user
- [ ] Enable UFW / provider firewall: allow **22, 80, 443, 2200/tcp**

### 1.3  DNS & TLS
- [ ] Purchase / configure domain (e.g. `netpilot.example.com`)
- [ ] Add *A* / *AAAA* records to VM IPs
- [ ] Defer Let's Encrypt until Nginx (Phase 3)

---

## Phase 2 – Backend Containerisation & Refactor

### 2.1  Codebase Updates
- [ ] Introduce `ROUTER_PORT` in `data/.env.example` and load in `backend/utils/ssh_client.py`
- [ ] Update `SSHClientManager.connect()` to use `self.router_port or 22`
- [ ] Make `backend/server.py` read `FLASK_ENV` for prod vs dev configs

### 2.2  Gunicorn & Docker
- [ ] Add `backend/gunicorn_config.py` (bind `127.0.0.1:5000`, 3 workers)
- [ ] Create `backend/Dockerfile` (python slim, pip install, copy code)
- [ ] Push image to registry `ghcr.io/<org>/netpilot-backend`

### 2.3  Compose Stack
- [ ] Install Docker + docker-compose (`compose v2` plugin) on VM
- [ ] Author root-level `docker-compose.yml` with services:
  * `backend` → image above, volume `./data:/app/data`
  * `nginx`    → reverse-proxy + static (from Phase 3)
- [ ] Create `systemd` unit `netpilot.service` to run `docker compose up -d`

---

## Phase 3 – Frontend Build & Delivery

### 3.1  Code Adjustments
- [ ] Add `.env.production` with `VITE_API_BASE_URL="https://netpilot.example.com"`
- [ ] Replace hard-coded `http://localhost:5000` in `src/**/*.{js,jsx}` with `import.meta.env.VITE_API_BASE_URL`
- [ ] Update `frontend/dashboard/vite.config.js` to expose env variable

### 3.2  Static Hosting
- [ ] Create multi-stage `frontend/Dockerfile` (build → serve with Nginx-alpine)
- [ ] Output files to `/usr/share/nginx/html`
- [ ] Mount build artefact in Compose `nginx` service

### 3.3  TLS Automation
- [ ] Install Certbot snap on VM
- [ ] Run `certbot --nginx -d netpilot.example.com` and renew

---

## Phase 4 – Reverse SSH Tunnel

### 4.1  Cloud-side Setup
- [ ] `adduser tunnel_user --disabled-password`
- [ ] `ssh-keygen -b4096 -f /home/tunnel_user/.ssh/id_rsa`
- [ ] Restrict `/home/tunnel_user/.ssh/authorized_keys` with `command="echo tunnel",no-port-forwarding,no-X11-forwarding`
- [ ] Edit `/etc/ssh/sshd_config`: `AllowUsers tunnel_user`, `GatewayPorts yes`, reload SSH

### 4.2  OpenWrt Router
- [ ] `opkg install openssh-client autossh`
- [ ] Copy private key from VM to `/root/.ssh/id_rsa_netpilot_cloud`
- [ ] Create `/etc/init.d/netpilot_tunnel` script (see proposal) & `chmod +x`
- [ ] `./etc/init.d/netpilot_tunnel enable && start` – verify with `ps | grep autossh`

### 4.3  Backend Validation
- [ ] Update cloud `.env`: `ROUTER_IP=127.0.0.1`, `ROUTER_PORT=2200`
- [ ] Test `ssh_manager.execute_command("echo ok")` succeeds via tunnel

---

## Phase 5 – CI / CD

### 5.1  GitHub Actions – Backend
- [ ] Workflow: on *push* to `main`, build backend Docker image & push to registry

### 5.2  GitHub Actions – Frontend
- [ ] Workflow: on *push* to `main`, build frontend image & push

### 5.3  Deploy Step
- [ ] Optional: add SSH deploy to VM (`docker compose pull && docker compose up -d`)

---

## Phase 6 – Observability

### 6.1  Centralised Logging
- [ ] Mount `/var/log/netpilot` from container to host
- [ ] Ship logs to provider service (Papertrail / CloudWatch)

### 6.2  Metrics & Alerts
- [ ] Enable provider-level VM monitoring (CPU, RAM, Disk)
- [ ] Add uptime monitor for `https://netpilot.example.com/health`

---

## Phase 7 – Data Backups

### 7.1  Strategy
- [ ] Create nightly cron: `tar -czf data-$(date).tgz /app/data`
- [ ] Upload to S3 / DigitalOcean Spaces with lifecycle policy

---

## Phase 8 – Security Hardening

### 8.1  Dependency Scanning
- [ ] Add `bandit` to backend CI and `npm audit` to frontend CI

### 8.2  Container Security
- [ ] Scan images with `trivy` in GitHub Actions

### 8.3  Credentials Management
- [ ] Migrate secrets to provider's secret store / GitHub Secrets

---

## Phase 9 – Testing & Validation

### 9.1  Local End-to-End
- [ ] Use `docker compose` locally to emulate cloud stack

### 9.2  Staging Validation
- [ ] Deploy to temporary subdomain `staging.netpilot.example.com`
- [ ] Run smoke tests (Postman collection in `postman/`)

### 9.3  Performance Test
- [ ] Run `k6` script: 200 concurrent requests to `/api/scan/router`

---

## Phase 10 – Production Roll-out

### 10.1  DNS Cut-over
- [ ] Point primary subdomain to production VM

### 10.2  Post-deploy Monitoring
- [ ] Monitor logs & alerts for 48 h

### 10.3  Documentation & Handover
- [ ] Update `README.md` with cloud deployment steps
- [ ] Conduct knowledge-transfer session with stakeholders

---

**Legend**
- **[ ]** – pending   |   **[x]** – done

Happy cloud-piloting! 🚀 