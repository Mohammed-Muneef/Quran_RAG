# Quranic RAG Semantic Search & Citation System

A production-grade, modular bilingual Retrieval-Augmented Generation (RAG) system for the Quran. The pipeline combines dense vector embeddings (ChromaDB) and lexical keyword matching (BM25) using **Reciprocal Rank Fusion (RRF)**, reranks candidates using a local **Cross-Encoder**, and serves cited answers grounded in Uthmani Arabic script, Sahih International English translation, and Ibn Kathir Tafsir via a premium Obsidian-Dark web dashboard.

---

## 🛠️ System Architecture

```
quran-rag/
├── data/
│   ├── raw/                  # Tanzil.net Uthmani Arabic + English raw layers
│   └── processed/            # Aligned bilingual verses + sliding-window chunks
├── ingest/
│   ├── download.py           # Tanzil / AlQuran corpus downloader
│   ├── merge.py              # Bilingual alignment & metadata merger (Surah, Juz, Revelation Type)
│   └── chunk.py              # Ayah-level + consecutive thematic window chunker
├── store/
│   └── chroma_store.py       # Persistent HNSW ChromaDB vector database indexer
├── retrieval/
│   ├── bm25.py               # Serialized rank-bm25 keyword indexer
│   ├── vector.py             # ChromaDB similarity search client
│   ├── expand.py             # LLM concept expander with local rule fallback & caches
│   ├── hybrid.py             # Parallel retrieval with RRF + keyword boosting
│   └── rerank.py             # Gemini / Cohere / CrossEncoder reranker chain
├── generation/
│   ├── prompt_loader.py      # Version-controlled prompt config loader
│   └── answer.py             # Citation formatter & groundedness checker
├── prompts/
│   └── v1.yaml               # Versioned YAML system prompts (v1 / v2 disclaimers)
├── eval/
│   ├── golden_dataset.json   # 60 verified benchmark Q&A pairs (Finance, Worship, Family, Ethics, etc.)
│   ├── citation_metric.py    # Custom citation precision/recall and hallucination checkers
│   └── run_eval.py           # Benchmark runner & quality gate validator
├── api/
│   ├── main.py               # FastAPI server exposing endpoints and static assets
│   └── static/               # Premium glassmorphic Obsidian-dark HTML, CSS, and JS
├── .github/workflows/
│   └── eval.yml              # CI/CD quality gate on PRs
├── Dockerfile                # Multi-stage Docker build with pre-built indexes
├── docker-compose.yml        # One-command local deployment
├── render.yaml               # Render.com deployment config
└── requirements.txt          # Python package dependencies
```

---

## 🚀 Getting Started

### 1. Installation

Set up the virtual environment and install the required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Ingest Data

Build the search indexes (Downloads the texts, structures them into single & thematic sliding-windows, computes the BM25 index, and embeds the translation into ChromaDB):
```bash
python ingest/download.py
python ingest/merge.py
python ingest/chunk.py
python store/chroma_store.py
```

### 3. Run Evaluations

Execute the validation suite against the 60 golden questions to verify citation accuracy and hallucination gates:
```bash
PYTHONPATH=. python eval/run_eval.py --sample 5
```

### 4. Launch the Web App

Start the FastAPI backend server:
```bash
PYTHONPATH=. python api/main.py
```
Open **[http://localhost:8000/](http://localhost:8000/)** in your web browser to use the Quranic RAG interface.

---

## 🔍 Retrieval & QA Pipeline Details

1. **Query Expansion**: The user query is expanded using Gemini (with OpenAI and local dictionary fallbacks) to bridge modern English to Quranic terminology (e.g. "interest" → "interest, riba, usury, debt, qard").
2. **Parallel Hybrid Search**: Parallel queries are run on ChromaDB (semantic dense) and BM25 (lexical sparse), combined using Reciprocal Rank Fusion ($k=60$) with keyword boosting for thematic metadata matches.
3. **Gemini Reranking**: Candidates are reranked using Gemini (which understands Islamic domain concepts), with Cohere and local CrossEncoder as fallbacks.
4. **Scholarly Answer Generation**:
   - Matches LLM API keys (Gemini / OpenAI) dynamically, falling back to an offline mock generator if no key is present to guarantee offline capability.
   - Enforces v2 JSON formatting including answer summary, citation array (Arabic, English, reference), and scholarly disclaimers.
   - Rejects ungrounded queries with exactly `"I cannot find a Quranic verse on this topic"`.
5. **Inspector Interface**: Clicking a citation opens a sliding inspector sidebar showing Arabic/English text side-by-side with confidence metrics.

---

## 🐳 Deployment

### Option A — Docker

```bash
# Build the image (pre-builds all indexes inside)
docker build -t quran-rag .

# Run with your API key
docker run -d -p 8000:8000 -e GEMINI_API_KEY=your_key_here quran-rag
```

### Option B — Docker Compose

```bash
# Add your GEMINI_API_KEY to .env file, then:
docker compose up -d
```

### Option C — Render (Free Tier)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service** → connect your repo
3. Render auto-detects `render.yaml` and configures everything
4. Add `GEMINI_API_KEY` in the **Environment** tab
5. Deploy — your app will be live at `https://quran-rag.onrender.com`

### Option D — Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set GEMINI_API_KEY=your_key_here
```

### Option E — Any VPS (DigitalOcean, Hetzner, etc.)

```bash
docker build -t quran-rag .
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key_here \
  --restart unless-stopped \
  quran-rag
```
# Quran_RAG
