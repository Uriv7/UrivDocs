#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  UrivDocs — Manual Deploy Script
#  Run on EC2 after cloning repo and filling .env
#  Usage: bash scripts/deploy_manual.sh
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }
info() { echo -e "${CYAN}[→]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }

cd /home/ubuntu/urivdocs

# ── Check .env exists ─────────────────────────────────────────
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Run: cp .env.example .env && nano .env"
    exit 1
fi
ok ".env file found"

# ── Create storage directories ────────────────────────────────
mkdir -p storage/uploads storage/vectordb storage/models
ok "Storage directories ready"

# ── Set up Nginx ──────────────────────────────────────────────
info "Installing Nginx config..."
sudo cp scripts/nginx_urivdocs.conf /etc/nginx/sites-available/urivdocs
sudo ln -sf /etc/nginx/sites-available/urivdocs /etc/nginx/sites-enabled/urivdocs
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
ok "Nginx configured"

# ── Build and start Docker containers ─────────────────────────
info "Building Docker images (first time takes ~5 minutes)..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose build
ok "Images built"

info "Starting containers..."
docker compose up -d
ok "Containers started"

# ── Wait for startup ──────────────────────────────────────────
info "Waiting for services to start (90 seconds)..."
for i in $(seq 1 90); do
    echo -n "."
    sleep 1
done
echo ""

# ── Pull LLM model ────────────────────────────────────────────
info "Pulling LLM model (llama3.2:3b — ~2GB, may take 10 minutes)..."
docker exec urivdocs-ollama ollama pull llama3.2:3b
ok "LLM model ready"

# ── Health check ──────────────────────────────────────────────
info "Running health check..."
if curl -sf http://localhost:8000/health > /dev/null; then
    ok "API is healthy!"
else
    warn "API health check failed. Checking logs..."
    docker compose logs --tail=50 api
    exit 1
fi

# ── Show status ───────────────────────────────────────────────
docker compose ps
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║   ✅ UrivDocs is Running!                       ║"
echo -e "╚══════════════════════════════════════════════════╝${RESET}"
echo ""

# Get EC2 public IP
EC2_IP=$(curl -sf http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")
echo "  App URL:    http://$EC2_IP"
echo "  API Health: http://$EC2_IP:8000/health"
echo "  API Docs:   http://$EC2_IP:8000/docs"
echo ""
echo "Open http://$EC2_IP in your browser!"
