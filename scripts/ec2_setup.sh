#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  UrivDocs — EC2 One-Time Setup Script
#
#  Run this ONCE on a fresh Ubuntu 22.04 EC2 instance.
#  Usage:
#    chmod +x scripts/ec2_setup.sh
#    bash scripts/ec2_setup.sh
#
#  What this does:
#    1. Updates system
#    2. Adds swap space (essential for LLM on t3.medium)
#    3. Installs Docker + Docker Compose
#    4. Installs Git, Nginx, Certbot, AWS CLI, Ollama
#    5. Hardens firewall
#    6. Creates app directory and clones repo
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }
info() { echo -e "${CYAN}[→]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }
fail() { echo -e "${RED}[✗]${RESET} $1"; exit 1; }
hr()   { echo -e "${CYAN}────────────────────────────────────────${RESET}"; }

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   UrivDocs — EC2 Production Setup Script    ║"
echo "  ║   Ubuntu 22.04 LTS                          ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# Require Ubuntu
grep -q "Ubuntu" /etc/os-release || fail "This script requires Ubuntu 22.04"

hr
echo -e "${BOLD}[1/12] System Update${RESET}"
hr
info "Updating package lists and upgrading..."
sudo apt-get update -y -qq
sudo apt-get upgrade -y -qq
ok "System updated"

hr
echo -e "${BOLD}[2/12] Swap Space (CRITICAL for LLM)${RESET}"
hr
if swapon --show | grep -q '/swapfile'; then
    ok "Swap already configured"
    free -h | grep Swap
else
    info "Creating 4GB swap (required to run LLM without OOM)..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    ok "4GB swap space created and enabled"
    free -h | grep Swap
fi

hr
echo -e "${BOLD}[3/12] Docker${RESET}"
hr
if command -v docker &>/dev/null; then
    ok "Docker already installed: $(docker --version)"
else
    info "Installing Docker CE..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker ubuntu
    sudo systemctl enable docker
    sudo systemctl start docker
    ok "Docker installed: $(docker --version)"
fi

hr
echo -e "${BOLD}[4/12] Docker Compose Plugin${RESET}"
hr
if docker compose version &>/dev/null; then
    ok "Docker Compose already available: $(docker compose version --short)"
else
    info "Installing Docker Compose plugin..."
    sudo apt-get install -y -qq docker-compose-plugin
    ok "Docker Compose: $(docker compose version --short)"
fi

# Optimize Docker log rotation
info "Configuring Docker log rotation..."
sudo tee /etc/docker/daemon.json > /dev/null << 'DOCKERJSON'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "live-restore": true
}
DOCKERJSON
sudo systemctl restart docker
ok "Docker log rotation configured"

hr
echo -e "${BOLD}[5/12] Git${RESET}"
hr
if command -v git &>/dev/null; then
    ok "Git already installed: $(git --version)"
else
    sudo apt-get install -y -qq git
    ok "Git: $(git --version)"
fi

hr
echo -e "${BOLD}[6/12] Nginx (Reverse Proxy)${RESET}"
hr
if command -v nginx &>/dev/null; then
    ok "Nginx already installed"
else
    sudo apt-get install -y -qq nginx
fi
sudo systemctl enable nginx
sudo systemctl start nginx
ok "Nginx running"

hr
echo -e "${BOLD}[7/12] Certbot (HTTPS)${RESET}"
hr
if command -v certbot &>/dev/null; then
    ok "Certbot already installed"
else
    sudo apt-get install -y -qq certbot python3-certbot-nginx
    ok "Certbot installed"
fi

hr
echo -e "${BOLD}[8/12] AWS CLI${RESET}"
hr
if command -v aws &>/dev/null; then
    ok "AWS CLI already installed: $(aws --version 2>&1)"
else
    info "Installing AWS CLI v2..."
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp/
    sudo /tmp/aws/install
    rm -rf /tmp/awscliv2.zip /tmp/aws/
    ok "AWS CLI: $(aws --version 2>&1)"
fi

hr
echo -e "${BOLD}[9/12] Monitoring Tools${RESET}"
hr
sudo apt-get install -y -qq htop curl wget unzip jq
ok "Tools installed: htop, curl, wget, unzip, jq"

hr
echo -e "${BOLD}[10/12] Firewall (UFW)${RESET}"
hr
sudo ufw --force enable
sudo ufw allow 22/tcp   comment 'SSH'
sudo ufw allow 80/tcp   comment 'HTTP'
sudo ufw allow 443/tcp  comment 'HTTPS'
sudo ufw allow 8000/tcp comment 'API direct access'
sudo ufw allow 3000/tcp comment 'UI direct access'
ok "Firewall configured"
sudo ufw status numbered

hr
echo -e "${BOLD}[11/12] App Directory${RESET}"
hr
APP_DIR="/home/ubuntu/urivdocs"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/storage/uploads"
mkdir -p "$APP_DIR/storage/vectordb"
mkdir -p "$APP_DIR/storage/models"
ok "App directories ready at $APP_DIR"

hr
echo -e "${BOLD}[12/12] Nginx Config${RESET}"
hr
# Configure Nginx reverse proxy if config exists
if [ -f "$APP_DIR/scripts/nginx_urivdocs.conf" ]; then
    sudo cp "$APP_DIR/scripts/nginx_urivdocs.conf" /etc/nginx/sites-available/urivdocs
    sudo ln -sf /etc/nginx/sites-available/urivdocs /etc/nginx/sites-enabled/urivdocs
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    ok "Nginx configured and reloaded"
else
    warn "Nginx config not found — run after cloning repo"
fi

# ── Final summary ─────────────────────────────────────────────────────────────
EC2_IP=$(curl -sf http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_IP")
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║   ✅ EC2 Setup Complete!                                ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "  System:     $(lsb_release -d | cut -f2)"
echo "  Docker:     $(docker --version)"
echo "  Compose:    $(docker compose version --short)"
echo "  EC2 IP:     $EC2_IP"
echo ""
echo -e "${YELLOW}IMPORTANT — Next steps:${RESET}"
echo ""
echo "  1. Log out and back in (for Docker group to apply):"
echo "     exit"
echo "     ssh -i urivdocs-key.pem ubuntu@$EC2_IP"
echo ""
echo "  2. Clone your repository:"
echo "     git clone https://github.com/YOUR_USERNAME/urivdocs.git /home/ubuntu/urivdocs"
echo "     cd /home/ubuntu/urivdocs"
echo ""
echo "  3. Set up Nginx:"
echo "     sudo cp scripts/nginx_urivdocs.conf /etc/nginx/sites-available/urivdocs"
echo "     sudo ln -sf /etc/nginx/sites-available/urivdocs /etc/nginx/sites-enabled/"
echo "     sudo rm -f /etc/nginx/sites-enabled/default"
echo "     sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "  4. Push to GitHub main branch → auto-deploys via GitHub Actions!"
echo ""
echo "  Disk / Memory status:"
df -h / && free -h
