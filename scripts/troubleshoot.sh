#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  UrivDocs — Troubleshoot Script
#  Run if something is not working
#  Usage: bash scripts/troubleshoot.sh
# ══════════════════════════════════════════════════════════════════

echo "=== UrivDocs Troubleshoot Report ==="
echo "Generated: $(date)"
echo ""

echo "── Docker Containers ───────────────────────────────────────"
docker compose ps 2>/dev/null || echo "ERROR: Docker compose failed. Is Docker running?"
echo ""

echo "── Container Health ─────────────────────────────────────────"
for c in urivdocs-api urivdocs-ui urivdocs-ollama; do
    status=$(docker inspect --format='{{.State.Status}}' $c 2>/dev/null || echo "not found")
    echo "  $c: $status"
done
echo ""

echo "── API Logs (last 30 lines) ─────────────────────────────────"
docker compose logs --tail=30 api 2>/dev/null || echo "No API container"
echo ""

echo "── Disk Space ───────────────────────────────────────────────"
df -h /
echo ""

echo "── Memory ───────────────────────────────────────────────────"
free -h
echo ""

echo "── Nginx Status ─────────────────────────────────────────────"
sudo systemctl status nginx --no-pager 2>/dev/null || echo "Nginx not running"
echo ""

echo "── API Health Check ─────────────────────────────────────────"
curl -sf http://localhost:8000/health && echo "" || echo "API not responding"
echo ""

echo "── LLM Models Available ─────────────────────────────────────"
docker exec urivdocs-ollama ollama list 2>/dev/null || echo "Ollama not available"
echo ""

echo "── Quick Fixes ──────────────────────────────────────────────"
echo "  Restart all:     docker compose restart"
echo "  Rebuild all:     docker compose down && docker compose up -d --build"
echo "  View API logs:   docker compose logs -f api"
echo "  Pull LLM model:  docker exec urivdocs-ollama ollama pull llama3.2:3b"
echo "  Nginx reload:    sudo systemctl reload nginx"
echo "  Free disk:       docker image prune -af"
