# Infra AI Assistant

AI-powered IT Infrastructure assistant with RAG (Retrieval-Augmented Generation). Upload vendor documentation, ask questions, compare vendors, generate configs, and troubleshoot issues — all powered by Claude AI.

## Features

- 🤖 **Smart Q&A** — Ask questions about IT infrastructure, get answers backed by your documentation
- 🔍 **Hybrid Search** — BM25 keyword + vector search with Reciprocal Rank Fusion
- 📊 **Vendor Comparison** — Compare multiple vendors side-by-side (Cisco vs Juniper, Dell vs IBM, etc.)
- ⚙️ **Config Generator** — Generate network/server configurations from documentation
- 🔧 **Troubleshooting Agent** — Multi-turn diagnosis with step-by-step fixes
- 📤 **Live Document Upload** — Drag & drop PDFs/HTMLs, instantly indexed
- 💬 **Multi-turn Chat** — Conversation memory for follow-up questions
- 📈 **Analytics Dashboard** — Query stats, indexed documents overview

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 16, Angular Material |
| Backend | Python, FastAPI |
| LLM | Anthropic Claude (claude-sonnet-4-20250514) |
| Vector DB | ChromaDB |
| Embeddings | BGE-base-en-v1.5 (sentence-transformers) |
| Search | Hybrid (BM25 + Vector + RRF) |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd infra-ai-assistant
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
set PYTHONPATH=src        # Windows
export PYTHONPATH=src     # Mac/Linux
python -m uvicorn rag_bot.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend/rag-bot-ui
npm install
npx ng serve
# Open http://localhost:4200
```

### Ingest Documents

Place your vendor PDFs/HTMLs in `data/vendor/<VendorName>/` then run:

```bash
# PDFs
python -m rag_bot.ingestion.pdf_loader

# HTMLs
python -m rag_bot.ingestion.html_loader
```

Or use the **Upload** page in the UI to drag & drop documents.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Ask a question (supports multi-turn) |
| POST | `/compare` | Compare vendors on a topic |
| POST | `/config-gen` | Generate configurations |
| POST | `/troubleshoot` | Troubleshooting agent |
| POST | `/upload` | Upload PDF/HTML document |
| GET | `/documents` | List indexed documents |
| DELETE | `/documents/{id}` | Remove a document |
| GET | `/analytics` | Query analytics |
| GET | `/health` | Health check |

## Project Structure

```
infra-ai-assistant/
├── src/rag_bot/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── config.py            # Configuration + vendor document registry
│   ├── retrieval/
│   │   └── retriever.py     # Hybrid search (BM25 + vector + RRF)
│   ├── generation/
│   │   └── generator.py     # Claude AI integration
│   ├── ingestion/
│   │   ├── pdf_loader.py    # PDF extraction + chunking
│   │   └── html_loader.py   # HTML extraction + chunking
│   └── session_manager.py   # Conversation memory
├── frontend/rag-bot-ui/     # Angular 16 app
│   └── src/app/
│       ├── components/      # Chat, Dashboard, Upload
│       ├── services/        # API service
│       └── models/          # TypeScript interfaces
├── data/vendor/             # Vendor documentation (PDFs/HTMLs)
├── requirements.txt
└── .env                     # API keys
```

## Supported Vendors (default)

- **Dell** — PowerEdge servers, OpenManage
- **Cisco** — Campus infrastructure, wireless, IP addressing
- **Juniper** — JunOS, network management
- **Fortinet** — FortiGate, FortiWeb, FortiOS
- **IBM** — Power Systems, HTTP Server, SPSS
- **EUC** — End User Computing solutions

## License

MIT
