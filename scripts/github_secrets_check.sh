#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  UrivDocs — GitHub Secrets Verification Script
#  Run this on EC2 after GitHub Actions deploys to verify secrets were injected
#  Usage: bash scripts/github_secrets_check.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }
fail() { echo -e "${RED}[✗]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }

cd /home/ubuntu/urivdocs

echo "━━━ GitHub Secrets → .env Verification ━━━"
echo ""

if [ ! -f .env ]; then
    fail ".env file not found — has GitHub Actions deployed yet?"
    exit 1
fi

PASS=0; FAIL=0
check_secret() {
    local key="$1"
    local value
    value=$(grep "^${key}=" .env 2>/dev/null | cut -d'=' -f2- || echo "")
    if [ -z "$value" ] || [ "$value" = "" ]; then
        fail "$key — MISSING or empty"
        FAIL=$((FAIL + 1))
    else
        # Mask value for display
        MASKED="${value:0:4}****"
        ok "$key = $MASKED (set)"
        PASS=$((PASS + 1))
    fi
}

check_secret "AWS_ACCESS_KEY_ID"
check_secret "AWS_SECRET_ACCESS_KEY"
check_secret "AWS_REGION"
check_secret "S3_BUCKET"
check_secret "CORS_ORIGINS"

echo ""
echo "━━━ Results: $PASS passed, $FAIL failed ━━━"
[ $FAIL -eq 0 ] && ok "All secrets injected correctly" || { fail "Fix missing secrets in GitHub → Settings → Secrets"; exit 1; }

echo ""
echo "━━━ Container Status ━━━"
docker compose ps
