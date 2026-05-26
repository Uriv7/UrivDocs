# UrivDocs — Complete Deployment Guide
## From Your Laptop → GitHub → AWS → Public Internet

---

# STEP 1 — PROJECT ANALYSIS

## What is UrivDocs?

| Property | Value |
|---|---|
| Type | Full-Stack AI Web Application |
| Backend | FastAPI (Python) — runs on port **8000** |
| Frontend | React + Vite (Nginx) — runs on port **3000** |
| AI/LLM | Ollama (llama3.2:3b) — runs on port **11434** |
| Vector DB | ChromaDB (local, embedded) |
| File Storage | AWS S3 (cloud) + local fallback |
| Containerized | Yes — Docker Compose (3 containers) |

## How Containers Work Together

```
Browser → Nginx (port 80/443)
              ├── / → React UI container (port 3000)
              ├── /api/ → FastAPI container (port 8000)
              └── /health → FastAPI container (port 8000)

FastAPI → Ollama container (port 11434) for LLM
FastAPI → ChromaDB (embedded, same container)
FastAPI → AWS S3 (cloud) for file storage
```

## AWS Services Used

| Service | Why |
|---|---|
| **EC2** | Runs Docker containers (your server) |
| **S3** | Stores uploaded files permanently |
| **IAM** | Manages AWS permissions securely |

---

# STEP 2 — ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR LAPTOP                           │
│   Code Editor → git push → GitHub Repository            │
└─────────────────────────┬───────────────────────────────┘
                          │ git push triggers
                          ▼
┌─────────────────────────────────────────────────────────┐
│              GITHUB ACTIONS CI/CD                       │
│   1. Validate code                                      │
│   2. SSH into EC2                                       │
│   3. git pull latest code                               │
│   4. docker compose build + up                          │
│   5. Health check                                       │
└─────────────────────────┬───────────────────────────────┘
                          │ SSH deploy
                          ▼
┌─────────────────────────────────────────────────────────┐
│              AWS EC2 (Ubuntu Server)                    │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  Nginx   │  │ React UI │  │    FastAPI Backend   │  │
│  │  :80/443 │→ │  :3000   │  │       :8000          │  │
│  └──────────┘  └──────────┘  └──────────┬───────────┘  │
│                                          │              │
│                               ┌──────────▼───────────┐  │
│                               │   Ollama LLM :11434  │  │
│                               │   (llama3.2:3b)      │  │
│                               └──────────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ boto3 SDK
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS S3 BUCKET                        │
│          stores uploaded PDFs, DOCX, etc.               │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTPS
┌─────────────────────────────────────────────────────────┐
│   PUBLIC INTERNET — accessible from any device          │
│   Mobile / Laptop / Tablet → https://yourdomain.com     │
└─────────────────────────────────────────────────────────┘
```

---

# STEP 3 — GITHUB SETUP

## 3.1 Create GitHub Account
Go to https://github.com → Sign up (free)

## 3.2 Create New Repository
1. Click **+** (top right) → **New repository**
2. Name: `urivdocs`
3. Visibility: **Private** (recommended — keeps your code safe)
4. Do NOT check "Add README" (you already have files)
5. Click **Create repository**

## 3.3 Push Code to GitHub

Open terminal in your `urivdocs` project folder:

```bash
# Initialize git (only first time)
git init

# Tell git who you are
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# Add all files (respects .gitignore)
git add .

# Save a snapshot with message
git commit -m "Initial commit: UrivDocs v1.1.0"

# Rename branch to main (GitHub standard)
git branch -M main

# Connect to GitHub (replace with YOUR repo URL)
git remote add origin https://github.com/YOUR_USERNAME/urivdocs.git

# Push code to GitHub
git push -u origin main
```

## 3.4 What Each Command Does

| Command | Meaning |
|---|---|
| `git init` | Starts tracking files in this folder |
| `git add .` | Stages all files for commit |
| `git commit -m "..."` | Saves a snapshot with a message |
| `git branch -M main` | Renames branch to "main" |
| `git remote add origin URL` | Links local project to GitHub |
| `git push -u origin main` | Uploads code to GitHub |

---

# STEP 4 — AWS ACCOUNT + IAM SETUP

## 4.1 Create AWS Account
Go to https://aws.amazon.com → Create account (free tier available)

## 4.2 Create IAM User (IMPORTANT — never use root account)

**Why not root?** Root account has unlimited power. If leaked, attacker can delete everything and run up huge bills. IAM user has limited permissions.

1. Go to **AWS Console** → Search "IAM" → Click IAM
2. Left sidebar → **Users** → **Create user**
3. Username: `urivdocs-deploy`
4. Click **Next**
5. Select **Attach policies directly**
6. Search and check: `AmazonEC2FullAccess`
7. Search and check: `AmazonS3FullAccess`
8. Click **Next** → **Create user**

## 4.3 Create Access Keys

1. Click on `urivdocs-deploy` user
2. Tab: **Security credentials**
3. Scroll to **Access keys** → **Create access key**
4. Use case: **CLI**
5. Check confirmation → **Next** → **Create access key**
6. **COPY BOTH VALUES NOW** — you cannot see secret key again!

```
Access Key ID:     AKIAIOSFODNN7EXAMPLE
Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## 4.4 Install AWS CLI on Your Laptop

**Mac:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```

**Windows:** Download from https://aws.amazon.com/cli/

## 4.5 Configure AWS CLI

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG...
Default region name: us-east-1
Default output format: json
```

Verify:
```bash
aws sts get-caller-identity
# Should show your account info
```

---

# STEP 5 — AWS S3 SETUP

## 5.1 Create S3 Bucket (for file uploads)

```bash
# Run this on your laptop (not EC2)
# Replace "yourname" with something unique
bash scripts/setup_s3.sh urivdocs-uploads-yourname us-east-1
```

This script:
- Creates a private S3 bucket
- Blocks all public access (files are secure)
- Enables versioning (keeps history)
- Creates uploads/ folder

## 5.2 What You'll Get

```
S3 Bucket: urivdocs-uploads-yourname
Structure:
  uploads/
    ├── document1.pdf
    ├── report.docx
    └── data.csv
```

Every file a user uploads goes here automatically.

---

# STEP 6 — AWS EC2 SETUP

## 6.1 Launch EC2 Instance

1. AWS Console → **EC2** → **Launch Instance**
2. Name: `urivdocs-server`
3. AMI (Operating System): **Ubuntu Server 22.04 LTS** (free tier eligible)
4. Instance type: **t3.medium** (2 vCPU, 4GB RAM) — minimum for llama3.2:3b
   - Free tier: t2.micro works for testing only (not enough RAM for LLM)
5. Key pair: **Create new key pair**
   - Name: `urivdocs-key`
   - Type: RSA
   - Format: .pem (Mac/Linux) or .ppk (Windows PuTTY)
   - Click **Create** → file downloads automatically → **SAVE THIS FILE**
6. Storage: Change to **30 GB** (models need space)
7. Click **Launch instance**

## 6.2 Configure Security Group (Firewall)

After launching, click your instance → **Security** → **Security groups** → **Edit inbound rules**

Add these rules:

| Type | Port | Source | Purpose |
|---|---|---|---|
| SSH | 22 | My IP | SSH access (only your IP) |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom TCP | 8000 | 0.0.0.0/0 | API (optional, for testing) |
| Custom TCP | 3000 | 0.0.0.0/0 | UI (optional, for testing) |

Click **Save rules**

## 6.3 Connect to EC2

```bash
# Fix PEM file permissions (required on Mac/Linux)
chmod 400 urivdocs-key.pem

# SSH into EC2 (replace with your EC2 Public IP)
ssh -i urivdocs-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Find your EC2 Public IP: AWS Console → EC2 → Your instance → **Public IPv4 address**

---

# STEP 7 — SERVER SETUP (run on EC2)

```bash
# After SSH-ing into EC2, run:
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/urivdocs/main/scripts/ec2_setup.sh | bash
```

OR manually:

```bash
# Update system
sudo apt-get update -y && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# IMPORTANT: Re-login for docker group to take effect
exit
ssh -i urivdocs-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Install Git + Nginx + Certbot
sudo apt-get install -y git nginx certbot python3-certbot-nginx htop

# Verify
docker --version       # Docker version 24.x.x
docker compose version # Docker Compose version v2.x.x
git --version          # git version 2.x.x
nginx -v               # nginx/1.18.x
```

---

# STEP 8 — DEPLOY APPLICATION MANUALLY (first time)

```bash
# On EC2: Clone your repo
git clone https://github.com/YOUR_USERNAME/urivdocs.git
cd urivdocs

# Create .env file with your credentials
cp .env.example .env
nano .env
```

Edit .env — fill in your values:
```env
LLM_MODEL=llama3.2:3b
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG...
AWS_REGION=us-east-1
S3_BUCKET=urivdocs-uploads-yourname
CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP
```

Save and exit: `Ctrl+X` → `Y` → `Enter`

```bash
# Build and start all containers
docker compose up -d --build

# Watch logs (Ctrl+C to stop watching)
docker compose logs -f

# Check containers are running
docker compose ps

# Pull LLM model (takes 5-10 minutes, ~2GB download)
docker exec urivdocs-ollama ollama pull llama3.2:3b

# Test the app
curl http://localhost:8000/health
```

**Access from browser:**
```
http://YOUR_EC2_PUBLIC_IP:3000
```

---

# STEP 9 — NGINX SETUP (Reverse Proxy)

**What is Nginx?** Think of Nginx as a traffic controller. Instead of users accessing your app on port 3000 or 8000, they access port 80 (standard web port). Nginx receives the request and forwards it to the right container.

```bash
# Copy Nginx config
sudo cp /home/ubuntu/urivdocs/scripts/nginx_urivdocs.conf /etc/nginx/sites-available/urivdocs

# Enable the site
sudo ln -sf /etc/nginx/sites-available/urivdocs /etc/nginx/sites-enabled/urivdocs

# Remove default site (conflicts)
sudo rm -f /etc/nginx/sites-enabled/default

# Test config (should say OK)
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable auto-start
sudo systemctl enable nginx
```

Now access: `http://YOUR_EC2_PUBLIC_IP` (no port number needed!)

---

# STEP 10 — HTTPS + DOMAIN SETUP

## 10.1 Get a Domain (optional but recommended)

Options (free/cheap):
- **Freenom** — free .tk/.ml domains
- **Namecheap** — cheap domains (~$1/year)
- **GoDaddy** — popular domain registrar

## 10.2 Point Domain to EC2

In your domain registrar → DNS settings → Add:

| Type | Name | Value |
|---|---|---|
| A | @ | YOUR_EC2_PUBLIC_IP |
| A | www | YOUR_EC2_PUBLIC_IP |

Wait 5-10 minutes for DNS propagation.

## 10.3 Enable HTTPS with Let's Encrypt (Free SSL)

```bash
# Replace yourdomain.com with your actual domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose option 2 (redirect HTTP to HTTPS)

# Verify auto-renewal works
sudo certbot renew --dry-run
```

Now your app is at: `https://yourdomain.com` ✅

---

# STEP 11 — GITHUB ACTIONS CI/CD SETUP

## 11.1 Add GitHub Secrets

Go to: GitHub → Your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets one by one:

| Secret Name | Value | Where to get it |
|---|---|---|
| `EC2_HOST` | `54.123.456.789` | EC2 Console → Public IPv4 |
| `EC2_USERNAME` | `ubuntu` | Always ubuntu for Ubuntu AMI |
| `SSH_PRIVATE_KEY` | Contents of `urivdocs-key.pem` | The .pem file you downloaded |
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | IAM → User → Access keys |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtn...` | IAM → User → Access keys |
| `AWS_REGION` | `us-east-1` | Your chosen AWS region |
| `S3_BUCKET` | `urivdocs-uploads-yourname` | The bucket you created |
| `DOMAIN_NAME` | `yourdomain.com` | Your domain (or EC2 IP) |

## 11.2 Get SSH Private Key Content

```bash
# Mac/Linux: Print key contents and copy everything
cat urivdocs-key.pem

# Copy the ENTIRE output including:
# -----BEGIN RSA PRIVATE KEY-----
# ... many lines ...
# -----END RSA PRIVATE KEY-----
```

Paste this entire content as the `SSH_PRIVATE_KEY` secret.

## 11.3 How CI/CD Works

Every time you do `git push origin main`:

```
1. GitHub detects the push
2. GitHub Actions starts automatically
3. Ubuntu machine starts (free, GitHub provides)
4. Code is validated
5. SSH connection to your EC2
6. Latest code pulled
7. Docker containers rebuilt
8. Health check runs
9. You get email if something fails
```

## 11.4 Test the Pipeline

```bash
# Make a small change to trigger deployment
echo "# Deployed!" >> README.md
git add README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main

# Watch the pipeline:
# GitHub → Your repo → Actions tab → See live logs
```

---

# STEP 12 — ENVIRONMENT VARIABLES REFERENCE

## Complete .env for Production

```env
# LLM
LLM_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://ollama:11434

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# Vector Store
VECTOR_STORE=chroma
CHROMA_PERSIST_DIR=/app/storage/vectordb

# Chunking
CHUNK_SIZE=256
CHUNK_OVERLAP=32
TOP_K=5
MIN_SCORE=0.15

# Storage
UPLOAD_DIR=/app/storage/uploads
MAX_UPLOAD_MB=2048

# API
CORS_ORIGINS=https://yourdomain.com,http://YOUR_EC2_IP

# AWS S3 (for file uploads)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET=urivdocs-uploads-yourname
```

---

# STEP 13 — MONITORING & LOGS

```bash
# Check all containers running
docker compose ps

# View API logs live
docker compose logs -f api

# View all logs
docker compose logs -f

# Check server resources
htop                    # CPU + RAM usage
df -h                   # Disk space
free -h                 # Memory

# Nginx status
sudo systemctl status nginx

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart everything
docker compose restart

# Stop everything
docker compose down

# Start fresh
docker compose up -d --build
```

---

# STEP 14 — TROUBLESHOOTING

## Error: Docker permission denied
```bash
sudo usermod -aG docker ubuntu
exit  # logout
# SSH back in
```

## Error: Port already in use
```bash
sudo lsof -i :8000        # find what's using port 8000
sudo kill -9 <PID>        # kill it
docker compose up -d      # restart
```

## Error: Nginx 502 Bad Gateway
```bash
# Containers not running
docker compose ps         # check status
docker compose up -d      # start if stopped
docker compose logs api   # check API errors
```

## Error: SSH Connection Refused
```bash
# Wrong IP — check EC2 console for current Public IP
# EC2 restarts may change IP unless you use Elastic IP
```

## Error: GitHub Actions Failed
```bash
# Go to: GitHub → Actions → Click failed job → Read logs
# Common fixes:
# - SSH_PRIVATE_KEY has extra spaces → paste again carefully
# - EC2 IP changed → update EC2_HOST secret
# - Docker build failed → check Dockerfile
```

## Error: LLM not responding
```bash
docker exec urivdocs-ollama ollama list   # check model downloaded
docker exec urivdocs-ollama ollama pull llama3.2:3b  # re-pull
docker compose restart api                # restart API
```

## Error: S3 upload failed
```bash
# Check credentials in .env
aws s3 ls s3://YOUR_BUCKET_NAME    # test S3 access locally
# Check IAM policy allows s3:PutObject
```

---

# STEP 15 — COLLEGE PRESENTATION

## 5-Minute Explanation

*"I built UrivDocs — a local AI document intelligence system. You upload any file — PDF, Word doc, CSV — and ask natural language questions. It finds exact answers and shows you which page they came from.*

*For deployment, I used a professional DevOps pipeline: Code lives on GitHub. When I push changes, GitHub Actions automatically deploys to AWS EC2. The app runs in Docker containers — three of them: the React frontend, the FastAPI backend, and Ollama running the LLaMA AI model.*

*Files users upload are stored in AWS S3 — the same service Netflix uses for video storage. Nginx handles all traffic routing. The whole thing is secured with HTTPS.*

*The AI never sends your data to the cloud — the LLM runs completely on our server."*

## 10-Minute Expansion

Add:
- Show the GitHub Actions pipeline running live
- Explain Docker containers vs VMs
- Show the S3 bucket with uploaded files
- Show Nginx routing diagram
- Explain the RAG (Retrieval Augmented Generation) pipeline

## Viva Questions & Answers

**Q: What is Docker?**
A: Docker packages an application and all its dependencies into a container. Unlike a VM, it shares the host OS kernel, making it lightweight and fast. We use 3 containers: React UI, FastAPI, and Ollama.

**Q: What is CI/CD?**
A: Continuous Integration means code is automatically tested when pushed. Continuous Deployment means it's automatically deployed to the server. We use GitHub Actions — whenever I `git push`, code goes live in ~2 minutes.

**Q: Why S3 for file uploads?**
A: EC2 storage is limited and not durable. S3 gives unlimited storage, 99.999999999% durability, and handles any file size. It's the industry standard for file storage.

**Q: What is Nginx?**
A: A reverse proxy — it receives all web traffic on port 80/443 and routes it to the right container. Users access one URL; Nginx decides if the request goes to React (frontend) or FastAPI (API).

**Q: What is IAM?**
A: Identity and Access Management — AWS's permission system. Instead of using the root (admin) account, we create specific users with only the permissions they need (principle of least privilege).

**Q: Why not just run it locally?**
A: Local means only you can access it. EC2 gives a public IP accessible from any device worldwide. CI/CD means updates deploy automatically without manual SSH.

**Q: What is RAG?**
A: Retrieval Augmented Generation — instead of the AI relying on training data, we first search the document for relevant chunks using vector embeddings, then pass those chunks to the LLM as context. This gives accurate, cited answers instead of hallucinations.

---

# STEP 16 — RESUME + INTERVIEW

## Resume Description

```
UrivDocs — AI Document Intelligence System (2024)
GitHub: github.com/YOUR_USERNAME/urivdocs
Live: https://yourdomain.com

• Built full-stack RAG (Retrieval Augmented Generation) app using FastAPI,
  React, and Ollama (LLaMA 3.2) enabling natural language Q&A over documents

• Deployed on AWS using Docker Compose with automated CI/CD pipeline via
  GitHub Actions — zero-downtime deployments on every git push

• Integrated AWS S3 for scalable document storage, ChromaDB for vector
  similarity search, and Nginx as reverse proxy with HTTPS/SSL

• Implemented streaming LLM responses (SSE), conversation history,
  relevance filtering, and source citations with exact page numbers

Tech: Python, FastAPI, React, Docker, AWS EC2, AWS S3, GitHub Actions,
      Nginx, ChromaDB, Ollama, sentence-transformers, Certbot (SSL)
```

## Skills Demonstrated

- **Docker** — containerization, multi-container apps, Docker Compose
- **AWS** — EC2, S3, IAM, security groups, regions
- **CI/CD** — GitHub Actions, automated testing, automated deployment
- **Linux** — Ubuntu server, SSH, systemctl, file permissions
- **Nginx** — reverse proxy, SSL termination, load balancing concepts
- **Python** — FastAPI, async programming, REST APIs
- **React** — modern frontend, Vite, SSE streaming
- **AI/ML** — RAG pipeline, embeddings, vector search, LLMs
- **Security** — HTTPS, IAM least privilege, .gitignore, secrets management

---

# STEP 17 — FINAL CHECKLIST

Before presenting, verify each item:

```
□ GitHub
  □ Repository created (public or private)
  □ All code pushed (git push origin main)
  □ .gitignore working (no .env, no node_modules)
  □ .github/workflows/deploy.yml present

□ AWS IAM
  □ IAM user created (not root)
  □ Access Key + Secret Key saved
  □ S3 permissions attached

□ AWS S3
  □ Bucket created
  □ Public access blocked
  □ Test upload works: aws s3 cp test.txt s3://your-bucket/

□ AWS EC2
  □ Ubuntu instance running
  □ Security groups configured (ports 22, 80, 443)
  □ SSH connection works
  □ 30GB storage

□ Server Setup
  □ Docker installed: docker --version
  □ Docker Compose: docker compose version
  □ Git installed: git --version
  □ Nginx installed: nginx -v

□ Application
  □ Repo cloned on EC2
  □ .env file created with real values
  □ docker compose up -d works
  □ All 3 containers running: docker compose ps
  □ LLM model pulled: ollama list
  □ Health check passes: curl localhost:8000/health

□ Nginx
  □ Config copied to /etc/nginx/sites-available/
  □ Site enabled (symlink created)
  □ nginx -t passes
  □ App accessible on port 80: http://YOUR_EC2_IP

□ HTTPS (if domain available)
  □ Domain points to EC2 IP
  □ Certbot runs successfully
  □ App accessible on: https://yourdomain.com

□ GitHub Actions
  □ All 8 secrets added
  □ Pipeline triggered and passed
  □ Green checkmark on Actions tab

□ Final Tests
  □ Open app from mobile phone
  □ Upload a PDF
  □ Ask a question
  □ Get cited answer
  □ Follow-up question works
```

---

# STEP 18 — AWS COST ESTIMATE

| Service | Type | Monthly Cost |
|---|---|---|
| EC2 t3.medium | Compute | ~$30/month |
| EC2 t2.micro (free tier) | Compute | **FREE** (12 months) |
| S3 storage | First 5GB | **FREE** |
| S3 storage | Per GB after | ~$0.023/GB |
| S3 requests | Per 1000 | ~$0.0004 |
| Data transfer | First 100GB | **FREE** |
| **Total estimate** | | **$0–$35/month** |

**For college project:** Use t2.micro (free tier) + S3 free tier = **$0/month**

---

# STEP 19 — QUICK COMMANDS REFERENCE

```bash
# ── Deploy ───────────────────────────────────────────────
git add . && git commit -m "update" && git push origin main

# ── EC2 Management ───────────────────────────────────────
docker compose up -d          # Start all containers
docker compose down           # Stop all containers
docker compose restart api    # Restart just API
docker compose build --no-cache && docker compose up -d  # Full rebuild

# ── Logs ─────────────────────────────────────────────────
docker compose logs -f api    # API logs live
docker compose logs -f        # All logs live
docker compose ps             # Container status

# ── LLM ──────────────────────────────────────────────────
docker exec urivdocs-ollama ollama list         # List models
docker exec urivdocs-ollama ollama pull llama3.2:3b  # Pull model

# ── S3 ───────────────────────────────────────────────────
aws s3 ls s3://your-bucket/uploads/   # List files
aws s3 cp file.pdf s3://your-bucket/uploads/  # Upload

# ── Server ───────────────────────────────────────────────
sudo systemctl restart nginx  # Restart Nginx
sudo systemctl status nginx   # Nginx status
df -h                         # Disk space
htop                          # CPU/RAM
free -h                       # Memory
```

---

*UrivDocs Deployment Guide — v1.1.0*
*Built for college project presentation — covers GitHub + AWS EC2 + S3 + CI/CD*
