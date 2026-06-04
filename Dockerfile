# Lightweight Dockerfile for Render free tier (512MB RAM)
# Uses Gemini API for embeddings & reranking (no local ML models)
FROM python:3.11-slim

WORKDIR /app

# Install only lightweight dependencies (skip sentence-transformers for RAM savings)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    requests tqdm chromadb google-genai fastapi uvicorn \
    python-dotenv rank-bm25 pyyaml openai cohere && \
    rm -rf /root/.cache/pip

# Copy application code
COPY ingest/ ./ingest/
COPY store/ ./store/
COPY retrieval/ ./retrieval/
COPY generation/ ./generation/
COPY prompts/ ./prompts/
COPY eval/ ./eval/
COPY api/ ./api/
COPY data/ ./data/
COPY .env.example .

# Pre-build BM25 index (lightweight, ~4MB)
ENV PYTHONPATH=/app
RUN python -c "from retrieval.bm25 import QuranBM25Index; QuranBM25Index()" 2>/dev/null || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
