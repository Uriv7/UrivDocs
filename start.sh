#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║     UrivDocs — Quick Start                                      ║
# ╚══════════════════════════════════════════════════════════════════╝
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
log()     { echo -e "${CYAN}▶${RESET} $1"; }
success() { echo -e "${GREEN}✓${RESET} $1"; }
warn()    { echo -e "${YELLOW}⚠${RESET} $1"; }
error()   { echo -e "${RED}✗${RESET} $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}  ◈ UrivDocs — Starting up${RESET}\n"

# ── Model selection ────────────────────────────────────────────────
# llama3.2:3b  = 1.3GB, ~2-5s response  ← DEFAULT (fast)
# llama3.2:3b  = 2.0GB, ~5-10s response ← Better quality
# llama3       = 4.7GB, ~30-60s response ← Slowest, highest quality
LLM_MODEL="${LLM_MODEL:-llama3.2:3b}"

echo -e "${BOLD}  Model: $LLM_MODEL${RESET}"
echo -e "  (Set LLM_MODEL=llama3.2:3b for better quality)\n"

# ── Step 1: Patch requirements.txt ────────────────────────────────
log "Patching requirements.txt..."
cat > requirements.txt << 'REQEOF'
setuptools>=70.0.0
wheel>=0.43.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9
pydantic>=2.7.1
pydantic-settings>=2.2.1
pymupdf>=1.24.3; python_version < "3.13"
pypdf>=4.2.0
python-docx>=1.1.2
python-pptx>=1.0.0
openpyxl>=3.1.2
pillow>=11.0.0
pytesseract>=0.3.10
beautifulsoup4>=4.12.3
lxml>=5.2.1
faster-whisper>=1.0.3
sentence-transformers>=3.0.0
einops>=0.7.0
tiktoken>=0.7.0
chromadb>=0.5.0
qdrant-client>=1.9.1
ollama>=0.2.0
aiofiles>=23.2.1
httpx>=0.27.0
tqdm>=4.66.4
loguru>=0.7.2
REQEOF
success "requirements.txt patched"

# ── Step 2: Find Python ────────────────────────────────────────────
log "Finding Python..."
PYTHON=""
for py in python3.12 python3.11 python3.13 python3.14 python3.10 python3 python; do
    if command -v "$py" &>/dev/null; then
        MINOR=$($py -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
        MAJOR=$($py -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
        [[ "$MAJOR" == "3" && "$MINOR" -ge 10 ]] && { PYTHON="$py"; break; }
    fi
done
[[ -z "$PYTHON" ]] && error "Python 3.10+ required"
success "Using: $($PYTHON --version)"

# ── Step 3: Virtual environment ────────────────────────────────────
log "Setting up virtual environment..."
if [[ ! -d ".venv" ]] || ! .venv/bin/python --version &>/dev/null 2>&1; then
    rm -rf .venv
    $PYTHON -m venv .venv
    success "Created .venv"
else
    success "Reusing .venv ($(.venv/bin/python --version))"
fi

PIP=".venv/bin/pip"
UVICORN=".venv/bin/uvicorn"

# ── Step 4: Install dependencies ──────────────────────────────────
log "Upgrading pip..."
$PIP install --upgrade pip -q 2>/dev/null

log "Installing core packages..."
$PIP install fastapi "uvicorn[standard]" python-multipart pydantic pydantic-settings -q 2>/dev/null
success "API framework installed"

$PIP install chromadb qdrant-client aiofiles httpx tqdm loguru -q 2>/dev/null
success "Storage/utils installed"

$PIP install --only-binary=:all: pillow 2>/dev/null || $PIP install "pillow>=11.0.0" -q 2>/dev/null
$PIP install python-docx "python-pptx>=1.0.0" openpyxl pytesseract beautifulsoup4 lxml pypdf -q 2>/dev/null
success "File parsers installed"

PY_MINOR=$(.venv/bin/python -c "import sys; print(sys.version_info.minor)")
PY_MAJOR=$(.venv/bin/python -c "import sys; print(sys.version_info.major)")
if [[ "$PY_MAJOR" == "3" && "$PY_MINOR" -lt 13 ]]; then
    $PIP install "pymupdf>=1.24.3" -q 2>/dev/null && success "PyMuPDF installed" || warn "PyMuPDF skipped"
fi

log "Installing ML packages..."
$PIP install "sentence-transformers>=3.0.0" tiktoken einops -q 2>/dev/null
success "ML packages installed"

$PIP install ollama faster-whisper -q 2>/dev/null
success "LLM packages installed"

# ── Step 5: Config ─────────────────────────────────────────────────
[[ ! -f ".env" ]] && cp .env.example .env 2>/dev/null && success "Created .env" || true
mkdir -p storage/uploads storage/vectordb storage/models

# ── Step 6: Ollama ─────────────────────────────────────────────────
log "Checking Ollama..."
if ! command -v ollama &>/dev/null; then
    warn "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
fi

OLLAMA_PID=""
if command -v ollama &>/dev/null; then
    if ! curl -sf http://localhost:11434 &>/dev/null; then
        log "Starting Ollama..."
        pkill -f "ollama serve" 2>/dev/null || true; sleep 1
        ollama serve > /tmp/urivdocs-ollama.log 2>&1 &
        OLLAMA_PID=$!; sleep 4
        success "Ollama started"
    else
        success "Ollama already running"
    fi

    # Pull the fast model if not present
    if ! ollama list 2>/dev/null | grep -q "$LLM_MODEL"; then
        log "Pulling $LLM_MODEL (fast model, ~2.0GB)..."
        ollama pull "$LLM_MODEL" && success "$LLM_MODEL ready" || {
            warn "$LLM_MODEL pull failed — trying llama3..."
            LLM_MODEL="llama3"
            ollama pull "$LLM_MODEL" 2>/dev/null || warn "Run: ollama pull $LLM_MODEL"
        }
    else
        success "$LLM_MODEL already available"
    fi

    # Pre-load model into RAM (so it's warm when first query arrives)
    log "Pre-loading $LLM_MODEL into RAM..."
    ollama run "$LLM_MODEL" "hi" --nowordwrap 2>/dev/null | head -1 || true
    success "Model loaded into RAM — first response will be fast!"
else
    warn "Ollama not available — install from https://ollama.com"
fi

# ── Step 7: Launch API ─────────────────────────────────────────────
cleanup() {
    echo -e "\n${YELLOW}Stopping UrivDocs...${RESET}"
    kill $API_PID 2>/dev/null || true
    [[ -n "${OLLAMA_PID}" ]] && kill $OLLAMA_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

log "Starting FastAPI backend..."
export PYTHONPATH="$SCRIPT_DIR"
export VECTOR_STORE="${VECTOR_STORE:-chroma}"
export CHROMA_PERSIST_DIR="${CHROMA_PERSIST_DIR:-$SCRIPT_DIR/storage/vectordb}"
export UPLOAD_DIR="${UPLOAD_DIR:-$SCRIPT_DIR/storage/uploads}"
export LLM_MODEL="$LLM_MODEL"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-all-MiniLM-L6-v2}"
export CORS_ORIGINS="http://localhost:5173,http://localhost:3000"

# 1 worker = shared singletons (Chroma, embedder, LLM all in same process)
$UVICORN api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --timeout-keep-alive 300 \
    --log-level warning &
API_PID=$!

log "Waiting for API (embedding + LLM loading into RAM)..."
for i in $(seq 1 90); do
    curl -sf http://localhost:8000/health > /dev/null 2>&1 && break
    echo -n "."; sleep 2
done; echo ""
success "API ready!"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗"
echo -e "║   ◈  UrivDocs Backend is Running!                    ║"
echo -e "╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  🔌  API    →  ${CYAN}http://localhost:8000${RESET}"
echo -e "  📚  Docs   →  ${CYAN}http://localhost:8000/docs${RESET}"
echo -e "  🤖  Model  →  ${BOLD}$LLM_MODEL${RESET} (loaded in RAM)"
echo ""
echo -e "  Open a NEW terminal and run:"
echo -e "  ${CYAN}bash start_ui.sh${RESET}"
echo ""
echo -e "  💡 For better quality: ${CYAN}LLM_MODEL=llama3.2:3b bash start.sh${RESET}"
echo -e "${YELLOW}  Press Ctrl+C to stop${RESET}\n"
wait $API_PID
