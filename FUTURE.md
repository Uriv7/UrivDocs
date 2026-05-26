# UrivDocs — Future Roadmap

> Last updated: May 2026
> Current version: 1.1.0

---

## ✅ Already Built (v1.1.0)

- Upload any file: PDF, DOCX, CSV, TXT, MD, HTML, Images (OCR), Audio/Video
- Ask questions in plain English, get cited answers (page, section, score)
- **Strict grounding** — LLM only answers from document context, never hallucinates
- **Relevance filtering** — off-topic questions get "not found" instead of wrong answers
- **Chat resets** when switching between documents
- Real-time SSE token streaming with typing cursor + stop button
- Embedding model pre-warmed at startup (zero cold-start on first query)
- LLM pre-loaded into RAM via keep_alive=-1 (no delay between queries)
- Default: llama3.2:1b (~2-5s response), configurable to larger models
- ChromaDB (local) and Qdrant (hosted) vector stores
- Docker + local setup (single bash command)
- SEO-ready React frontend (OG tags, JSON-LD, sitemap, PWA manifest)
- Live upload progress with polling
- Multi-file support with per-document filtered queries

---

## 🚀 Phase 2 — Accuracy & Context (Next 4 weeks)

### 2.1 Conversation Memory (Follow-up Questions)
- **Problem:** "Tell me more about that" doesn't work — each query is stateless.
- **Fix:** Send last 3-5 messages as context with each new query.
- **Files:** `api/routes/query.py`, `ChatBox.jsx`, `api/schemas.py`
- **Impact:** Natural multi-turn conversations about documents

### 2.2 Cross-Encoder Re-Ranking
- **Problem:** Vector retrieval sometimes returns loosely related chunks.
- **Fix:** After retrieving top-10, re-rank with `cross-encoder/ms-marco-MiniLM-L-6-v2`.
  Only top-3 re-ranked results go to LLM.
- **Files:** `vectorstore/retriever.py` → add rerank step
- **Impact:** ~40% better answer accuracy with near-zero extra latency

### 2.3 Hybrid Search (Vector + BM25)
- **Problem:** Exact terms (product codes, names, IDs) don't always match by embedding.
- **Fix:** BM25 keyword index alongside Chroma, merge via Reciprocal Rank Fusion.
- **Files:** New `vectorstore/bm25_store.py`, update `retriever.py`
- **Impact:** Much better recall for specific technical terms

### 2.4 Query Rewriting
- **Problem:** Short/ambiguous queries ("what about pricing?") retrieve poor chunks.
- **Fix:** Use LLM to expand query to 2-3 variants before embedding.
- **Files:** New `models/query_rewriter.py`, update `retriever.py`

### 2.5 GPU / Apple Silicon Acceleration
- **What:** Auto-detect MPS (Apple Silicon) or CUDA (NVIDIA) for embeddings.
- **How:** `EMBEDDING_DEVICE=mps` on Mac, `cuda` on NVIDIA — 5-10x speedup.
- **Files:** `ingestion/embedder.py`, `start.sh` auto-detect logic

---

## 🎯 Phase 3 — User Experience (Weeks 5-8)

### 3.1 Persistent Conversation History
- Save all chats to local SQLite. Browse, search, resume past conversations.
- New `api/routes/history.py`, `History.jsx` sidebar section

### 3.2 PDF / Document Preview with Highlighted Source
- When clicking a source citation, render the actual PDF page with the
  matched paragraph highlighted using `pdf.js`.
- New `DocumentPreview.jsx`, `api/routes/preview.py`

### 3.3 One-Click Document Summary
- Button on each document: generates structured summary (topics, findings,
  key dates, conclusions) using map-reduce for large docs.
- New `api/routes/summarize.py`, `SummaryView.jsx`

### 3.4 Smart Auto-Suggested Questions
- After indexing, auto-generate 5 questions specific to that document.
- Shown in the empty chat state instead of generic suggestions.
- `api/routes/upload.py` → generate questions post-ingestion

### 3.5 Dark / Light Mode Toggle
- CSS variables already structured. Add toggle button top-right.
- `index.css`, `App.jsx`, new `ThemeToggle.jsx`

### 3.6 Mobile Responsive Layout
- Collapsible sidebar drawer, full-screen chat on mobile.
- CSS media queries in `Sidebar.jsx`, `ChatBox.jsx`, `index.css`

### 3.7 Keyboard Shortcuts
- `Cmd+K` → focus input, `Cmd+U` → upload, `Esc` → close viewer
- Global keydown in `App.jsx`

---

## 🔧 Phase 4 — Advanced RAG (Weeks 9-12)

### 4.1 Semantic Chunking
- Split at semantic boundaries (paragraph/topic change) instead of fixed windows.
- Better context preservation, fewer mid-sentence cuts.
- `ingestion/chunker.py` complete rewrite

### 4.2 Table & Structured Data Understanding
- Extract tables from PDFs/DOCX, answer "What was revenue in Q3?"
- `camelot-py` or `pdfplumber`, new `ingestion/parsers/table.py`

### 4.3 Image / Diagram Understanding
- Vision model (llava via Ollama) for "What does this diagram show?"
- `ingestion/parsers/image.py`, `models/llm.py` multimodal

### 4.4 Citation Deep-Link
- Each citation clicks directly to the PDF page at the exact paragraph.
- Store char offsets in chunks, use pdf.js annotation layer.

### 4.5 Answer Confidence Indicator
- Show "High / Medium / Low confidence" based on retrieval scores.
- Badge on each answer bubble in `ChatBox.jsx`

### 4.6 Agentic Multi-Step Reasoning
- For complex queries, LLM makes multiple retrieval calls autonomously.
- "Compare X and Y across all uploaded documents" style queries.

---

## 🌐 Phase 5 — Deployment & Sharing (Weeks 13-16)

### 5.1 Multi-User Auth
- Username/password login, per-user document collections.
- JWT tokens, SQLite user table, Chroma namespaces per user.

### 5.2 Shareable Document Collections
- Share a curated set of documents via a public link.
- Others can query without uploading — read-only access.

### 5.3 REST API with API Keys
- Full documented API for third-party integrations.
- API key management, rate limiting.

### 5.4 CLI Tool
- `urivdocs ask "question" --file doc.pdf` — terminal usage.
- Python Click CLI using the same pipeline.

### 5.5 Browser Extension
- Highlight webpage text → "Ask UrivDocs" → auto-saves + opens chat.

### 5.6 One-Command VPS Deploy
- Ansible playbook for Ubuntu: HTTPS, nginx, systemd, auto-renew certs.
- `deploy/setup-vps.sh`

---

## 🐛 Known Issues & Status

| Issue | Priority | Status |
|---|---|---|
| Wrong answers on off-topic questions | 🔴 Critical | ✅ Fixed in v1.1.0 (relevance filter + strict prompt) |
| Chat doesn't reset on doc switch | 🔴 Critical | ✅ Fixed in v1.1.0 (key prop remount) |
| Cold-start delay on first query | 🟡 High | ✅ Mostly fixed (keep_alive + warmup) |
| No follow-up question support | 🟡 High | 📋 Planned Phase 2.1 |
| No mobile UI | 🟡 Medium | 📋 Planned Phase 3.6 |
| Large PDF (>100MB) slow embed | 🟡 Medium | Will add async progress |
| No dark/light mode toggle | 🟢 Low | 📋 Planned Phase 3.5 |
| Audio transcription slow | 🟢 Low | faster-whisper already faster |

---

## 📊 Performance Targets

| Metric | v1.0 | v1.1 (now) | Target v2.0 |
|---|---|---|---|
| First token latency | 30-60s | 2-5s (1b model) | <2s |
| Answer accuracy | ~55% | ~65% | ~85% |
| Max file size | 2GB | 2GB | 10GB |
| Off-topic rejection | ❌ None | ✅ Score filter | ✅ + reranker |
| Concurrent users | 1 | 1 | 10+ |
| Supported formats | 8 | 8 | 15+ |

---

## 💡 How to Contribute

1. **Bug reports** — include full error from terminal + steps to reproduce
2. **Feature requests** — describe your use case
3. **Code** — follow existing patterns, add a test in `tests/`
4. **Docs** — improve README or inline comments

---

*UrivDocs — Privacy-first AI. Your data never leaves your machine.*
