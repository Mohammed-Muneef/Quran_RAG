# ---- Build Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY ingest/ ./ingest/
COPY store/ ./store/
COPY retrieval/ ./retrieval/
COPY generation/ ./generation/
COPY prompts/ ./prompts/
COPY eval/ ./eval/
COPY api/ ./api/
COPY data/ ./data/
COPY requirements.txt .
COPY .env.example .

# Pre-build the BM25 index and ChromaDB store during image build
# This avoids slow cold starts in production
RUN python -c "from retrieval.bm25 import QuranBM25Index; QuranBM25Index()"

# Note: ChromaDB store requires the embedding model to be loaded at runtime,
# so we pre-download the model weights instead
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Build ChromaDB index
RUN python -c "from store.chroma_store import QuranChromaStore; import json; \
    chunks = json.load(open('data/processed/chunks.json')); \
    store = QuranChromaStore(); store.upsert_chunks(chunks)"

EXPOSE 8000

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with production settings (no reload, workers based on CPU cores)
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
