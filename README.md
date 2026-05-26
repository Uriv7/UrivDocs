# ◈ UrivDocs

**Local AI document intelligence** — upload any file, ask any question, get cited answers with exact page numbers. Runs 100% on your machine. No cloud, no API keys, complete privacy.

---

## ✨ Features

- 📄 Upload **any file** — PDF (multi-GB), DOCX, CSV, TXT, MD, HTML, Images (OCR), Audio/Video
- 💬 Ask **natural language questions** across all documents
- 📍 Answers cite **exact page numbers, sections, and relevance scores**
- 🔒 **100% local** — no data ever leaves your machine
- ⚡ **Streaming responses** — see tokens appear as they generate
- 🧠 **Strict grounding** — never hallucinates, says "not found" when info isn't in docs
- 🔄 **Per-document chat** — separate fresh chat for each document
- 🐳 **Docker + local** setup — one command to run everything

---

## 🚀 Quick Start (Recommended)

```bash
# Terminal 1 — install everything + start backend
bash start.sh

# Terminal 2 — start frontend
bash start_ui.sh
```

Open **http://localhost:5173**

---

## 🐳 Docker Mode

```bash
bash setup.sh          # auto-detects Docker, builds + starts everything
open http://localhost:3000
```

---

## 🤖 LLM Models

| Model | RAM | Speed | Quality |
|---|---|---|---|
| `llama3.2:3b` | 2.0GB | ~5-10s | ✅ **Default — good balance** |
| `llama3.2:1b` | 1.3GB | ~2-5s  | Fast, basic quality |
| `llama3`      | 4.7GB | ~30-60s | Best quality, slow |

```bash
# Use a different model:
LLM_MODEL=llama3 bash start.sh
```

---

## 📁 Supported File Types

| Format | Parser | Notes |
|---|---|---|
| PDF | PyMuPDF + pypdf fallback | Streamed — handles 2GB+ |
| DOCX/DOC | python-docx | Preserves headings |
| CSV/TSV | stdlib csv | Grouped into pages |
| PNG/JPG/TIFF | Tesseract OCR | Text extraction |
| MP3/WAV/MP4 | faster-whisper | Auto-transcribes |
| TXT/MD/HTML | Generic parser | Strips HTML tags |

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key settings:
```env
LLM_MODEL=llama3.2:3b      # LLM model
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=256              # tokens per chunk (256 = best for factual docs)
MIN_SCORE=0.15              # minimum relevance score (lower = more permissive)
TOP_K=5                     # chunks retrieved per query
```

---

## 🏗️ Architecture

```
User → React UI → FastAPI → [File Parser] → [Chunker] → [Embedder] → ChromaDB
                          ↘ [Retriever] → [LLM (Ollama)] → Streamed Answer + Sources
```

---

## 🧪 Running Tests

```bash
source .venv/bin/activate
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## 📋 Project Structure

```
urivdocs/
├── api/              # FastAPI backend
├── ingestion/        # File parsers + chunker + embedder
├── vectorstore/      # ChromaDB + Qdrant stores
├── models/           # LLM + prompt builder
├── ui/               # React + Vite frontend
├── storage/          # uploads + vectordb (gitignored)
├── tests/            # test suite
├── start.sh          # local start script
├── start_ui.sh       # frontend start script
├── setup.sh          # master setup (auto Docker/local)
├── FUTURE.md         # roadmap
└── docker-compose.yml
```

---

## 💡 Tips

- **Delete and re-index** when you change `CHUNK_SIZE`: `rm -rf storage/vectordb/*`
- **Per-document queries**: click a document in sidebar to filter answers to that file only
- **Stop generation**: red ■ button appears while LLM is generating
- **Switch docs**: chat resets automatically when you select a different document

---

## 🛡️ Privacy

- All processing happens locally on your machine
- No telemetry, no analytics, no external API calls
- Documents are stored in `storage/uploads/` — delete anytime
- Vector index stored in `storage/vectordb/` — delete to clear memory

---

*UrivDocs v1.1.0 — Built for privacy-first AI*
