#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║               UrivDocs — Master Setup & Run Script v4                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'; PURPLE='\033[0;35m'
log()     { echo -e "${CYAN}[UrivDocs]${RESET} $1"; }
success() { echo -e "${GREEN}[✓]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[✗]${RESET} $1"; exit 1; }
header()  { echo -e "\n${BOLD}${PURPLE}$1${RESET}\n────────────────────────────────────────"; }

echo -e "${BOLD}${PURPLE}"
cat << 'BANNER'
  ██╗   ██╗██████╗ ██╗██╗   ██╗██████╗  ██████╗  ██████╗███████╗
  ██║   ██║██╔══██╗██║██║   ██║██╔══██╗██╔═══██╗██╔════╝██╔════╝
  ██║   ██║██████╔╝██║██║   ██║██║  ██║██║   ██║██║     ███████╗
  ██║   ██║██╔══██╗██║╚██╗ ██╔╝██║  ██║██║   ██║██║     ╚════██║
  ╚██████╔╝██║  ██║██║ ╚████╔╝ ██████╔╝╚██████╔╝╚██████╗███████║
   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═════╝  ╚═════╝  ╚═════╝╚══════╝
BANNER
echo -e "${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
OS="$(uname -s)"; ARCH="$(uname -m)"
MODE="${1:-auto}"; LLM_MODEL="${2:-llama3}"
log "OS: $OS/$ARCH | Mode: $MODE"

# ══════════════════════════════════════════════════════════════
# STEP 1 — Self-heal ALL files
# ══════════════════════════════════════════════════════════════
header "Step 1 — Auto-patching all files"

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
success "requirements.txt"

cat > Dockerfile.api << 'DEOF'
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-eng ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p storage/uploads storage/vectordb storage/models
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
DEOF
success "Dockerfile.api"

cat > docker-compose.yml << 'COMPOSEEOF'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: urivdocs-ollama
    ports:
      - "11434:11434"
    volumes:
      - urivdocs_models:/root/.ollama
    restart: unless-stopped
  qdrant:
    image: qdrant/qdrant:latest
    container_name: urivdocs-qdrant
    ports:
      - "6333:6333"
    volumes:
      - urivdocs_qdrant:/qdrant/storage
    restart: unless-stopped
    profiles: ["qdrant"]
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: urivdocs-api
    ports:
      - "8000:8000"
    volumes:
      - urivdocs_uploads:/app/storage/uploads
      - urivdocs_vectordb:/app/storage/vectordb
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - CHROMA_PERSIST_DIR=/app/storage/vectordb
      - UPLOAD_DIR=/app/storage/uploads
      - LLM_MODEL=llama3
      - EMBEDDING_MODEL=all-MiniLM-L6-v2
      - VECTOR_STORE=chroma
      - CHUNK_SIZE=256
      - CHUNK_OVERLAP=32
      - TOP_K=5
      - MAX_UPLOAD_MB=2048
      - CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    depends_on:
      - ollama
    restart: unless-stopped
  ui:
    build:
      context: ./ui
      dockerfile: Dockerfile.ui
    container_name: urivdocs-ui
    ports:
      - "3000:80"
    depends_on:
      - api
    restart: unless-stopped
volumes:
  urivdocs_uploads:
  urivdocs_vectordb:
  urivdocs_models:
  urivdocs_qdrant:
COMPOSEEOF
success "docker-compose.yml"

mkdir -p ingestion/parsers
cat > ingestion/parsers/audio.py << 'AUDIOEOF'
"""UrivDocs — audio parser using faster-whisper"""
from pathlib import Path
from typing import List
from loguru import logger
from ingestion.parsers.base import BasePage
class AudioParser:
    _model = None
    def _get_model(self):
        if AudioParser._model is None:
            try:
                from faster_whisper import WhisperModel
                AudioParser._model = WhisperModel("base", device="cpu", compute_type="int8")
            except ImportError:
                return None
        return AudioParser._model
    def parse(self, path: Path) -> List[BasePage]:
        model = self._get_model()
        if not model:
            return [BasePage(text="[Audio transcription unavailable — run: pip install faster-whisper]", page_number=1)]
        try:
            segments, info = model.transcribe(str(path), beam_size=5)
            pages, buf, pn, we = [], [], 1, 60.0
            for seg in segments:
                buf.append(seg.text.strip())
                if seg.end >= we:
                    pages.append(BasePage(text=" ".join(buf), page_number=pn))
                    buf, pn, we = [], pn+1, we+60.0
            if buf: pages.append(BasePage(text=" ".join(buf), page_number=pn))
            return pages
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return []
AUDIOEOF
success "audio.py"

cat > ingestion/parsers/pdf.py << 'PDFEOF'
"""UrivDocs — pdf.py: PyMuPDF with pypdf fallback"""
from pathlib import Path
from typing import List
from loguru import logger
from ingestion.parsers.base import BasePage
class PDFParser:
    def parse(self, path: Path) -> List[BasePage]:
        try:
            import fitz
            pages = []
            doc = fitz.open(str(path))
            for i in range(doc.page_count):
                page = doc.load_page(i)
                text = page.get_text("text")
                if not text.strip():
                    blocks = page.get_text("blocks")
                    text = "\n".join(b[4] for b in blocks if isinstance(b[4], str))
                if text.strip():
                    pages.append(BasePage(text=text.strip(), page_number=i+1))
                page = None
            doc.close()
            logger.info(f"PyMuPDF: {len(pages)} pages from {path.name}")
            return pages
        except ImportError:
            logger.warning("PyMuPDF not available — using pypdf fallback")
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e} — using pypdf")
        try:
            from pypdf import PdfReader
            pages = []
            reader = PdfReader(str(path))
            for i, p in enumerate(reader.pages):
                text = p.extract_text() or ""
                if text.strip():
                    pages.append(BasePage(text=text.strip(), page_number=i+1))
            logger.info(f"pypdf: {len(pages)} pages from {path.name}")
            return pages
        except Exception as e:
            logger.error(f"Both PDF parsers failed: {e}")
            return []
PDFEOF
success "pdf.py"
success "All files patched ✓"

# ══════════════════════════════════════════════════════════════
# STEP 2 — Mode detection
# ══════════════════════════════════════════════════════════════
if [[ "$MODE" == "auto" ]]; then
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        MODE="docker"
    else
        MODE="local"
    fi
fi
log "Mode: ${BOLD}$MODE${RESET}"

# ══════════════════════════════════════════════════════════════
# DOCKER MODE
# ══════════════════════════════════════════════════════════════
if [[ "$MODE" == "docker" ]]; then
    header "Docker Mode"
    [[ ! -f ".env" ]] && cp .env.example .env 2>/dev/null || echo "" > .env
    mkdir -p storage/uploads storage/vectordb storage/models
    log "Cleaning old containers..."
    docker compose down --remove-orphans 2>/dev/null || true
    docker builder prune -af 2>/dev/null || true
    log "Building images (no-cache)..."
    docker compose build --no-cache
    log "Starting services..."
    docker compose up -d
    log "Waiting for API (model warming up)..."
    for i in $(seq 1 80); do
        curl -sf http://localhost:8000/health > /dev/null 2>&1 && break
        echo -n "."; sleep 3
    done; echo ""
    success "API ready!"
    log "Pulling $LLM_MODEL..."
    docker exec urivdocs-ollama ollama pull "$LLM_MODEL" \
        && success "Model ready!" \
        || warn "Run: docker exec urivdocs-ollama ollama pull $LLM_MODEL"
    command -v open &>/dev/null && open http://localhost:3000 || true
    echo -e "\n${GREEN}◈ UrivDocs → http://localhost:3000${RESET}\n"
    exit 0
fi

# ══════════════════════════════════════════════════════════════
# LOCAL MODE — delegate to start.sh
# ══════════════════════════════════════════════════════════════
header "Local Mode"
exec bash "$SCRIPT_DIR/start.sh"
