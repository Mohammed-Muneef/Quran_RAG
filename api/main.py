#!/usr/bin/env python3
import os
import sys
import time
import json
import requests
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from retrieval.hybrid import QuranHybridSearch
from retrieval.rerank import rerank_chunks
from generation.answer import generate_answer
from store.chroma_store import QuranChromaStore
from langfuse import observe, get_client

# Initialize FastAPI App
app = FastAPI(
    title="Quran RAG Production API",
    description="Production-grade cited Quranic QA RAG search pipeline."
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global retrieval components
DB_PATH = ".chroma"
try:
    if not os.path.exists(DB_PATH):
        print(f"Warning: Database path '{DB_PATH}' not found. Building it now...")
        import json
        chunks_path = Path("data/processed/chunks.json")
        if chunks_path.exists():
            with open(chunks_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            temp_store = QuranChromaStore(db_path=DB_PATH)
            temp_store.upsert_chunks(chunks)
            print("Database built successfully.")
        else:
            print(f"Error: {chunks_path} not found. Cannot build database.")
            
    hybrid_search = QuranHybridSearch()
    store = QuranChromaStore(db_path=DB_PATH)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error initializing search components: {e}")
    hybrid_search = None
    store = None

# Request and Response schemas
class AskRequest(BaseModel):
    question: str
    surah_filter: Optional[int] = None

class VerseCitation(BaseModel):
    ref: str
    arabic: str
    english: str

class AskResponse(BaseModel):
    answer: str
    verses: List[VerseCitation]
    disclaimer: str
    retrieval_time_ms: int

@app.post("/ask", response_model=AskResponse)
@observe()
def ask_question(request: AskRequest):
    """
    RAG QA pipeline:
    1. Query Expansion (retrieval/expand.py)
    2. Parallel Hybrid Search (BM25 + Vector) (retrieval/hybrid.py)
    3. Cross-Encoder Reranking (retrieval/rerank.py)
    4. Answer Generation with Citations & Disclaimer (generation/answer.py)
    """
    if not hybrid_search:
        raise HTTPException(status_code=500, detail="Search indexing components are not initialized.")

    start_time = time.time()
    
    try:
        # Step 1, 2: Retrieve top 20 candidates (runs expand and hybrid search)
        candidates, expanded_query = hybrid_search.search(
            query=request.question,
            n_results=20,
            surah_number=request.surah_filter
        )
        print(f"Expanded query: '{expanded_query}'")
        
        # Step 3: Rerank top-20 to top-5 (use expanded query for better domain matching)
        top_5 = rerank_chunks(
            query=expanded_query,
            candidates=candidates,
            top_n=5
        )
        
        # Step 4: Run answer generation
        ans_data = generate_answer(
            query=request.question,
            context_chunks=top_5,
            version="v2"
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Map output schemas
        # If ungrounded fallback returned, format it cleanly
        if "error" in ans_data or ans_data.get("answer") == "I cannot find a Quranic verse on this topic":
            get_client().score_current_trace(name="failure", value=0, comment="Ungrounded")
            get_client().score_current_trace(name="citation_coverage", value=0)
            return AskResponse(
                answer="I cannot find a Quranic verse on this topic",
                verses=[],
                disclaimer="For a ruling specific to your situation, consult a qualified scholar (alim).",
                retrieval_time_ms=elapsed_ms
            )

        # Parse citation mappings
        citation_list = []
        for cit in ans_data.get("citations", []):
            citation_list.append(VerseCitation(
                ref=f"{cit['surah']} ({cit['ayah']})",
                arabic=cit["text_ar"],
                english=cit["text_en"]
            ))

        # Extract clean summary without the disclaimer string (API serves them separately)
        raw_answer = ans_data.get("answer", "")
        clean_summary = raw_answer.split("\n\nFor a ruling")[0].strip()
        
        get_client().score_current_trace(name="failure", value=0, comment="Success")
        get_client().score_current_trace(name="citation_coverage", value=1 if len(citation_list) > 0 else 0)

        return AskResponse(
            answer=clean_summary,
            verses=citation_list,
            disclaimer="For a ruling specific to your situation, consult a qualified scholar (alim).",
            retrieval_time_ms=elapsed_ms
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        get_client().score_current_trace(name="failure", value=1, comment=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """
    Verifies that the collection is healthy and returns indexing status.
    """
    if store and store.collection:
        count = store.collection.count()
        return {"status": "ok", "chunks_indexed": count}
    return {"status": "warning", "detail": "Vector store not initialized"}

_METRICS_CACHE = {"data": None, "timestamp": 0}

@app.get("/api/metrics")
def get_sre_metrics():
    """
    Fetches SRE dashboard metrics from Langfuse API v2.
    Proxies requests securely using server-side keys.
    Results are cached for 60 seconds to prevent 429 rate limits.
    """
    global _METRICS_CACHE
    import time
    if time.time() - _METRICS_CACHE["timestamp"] < 60 and _METRICS_CACHE["data"]:
        return _METRICS_CACHE["data"]
        
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    
    if not pk or not sk:
        raise HTTPException(status_code=500, detail="Langfuse keys not configured.")
        
    auth = (pk, sk)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    
    def fetch_metric(query_dict):
        url = f"{host}/api/public/v2/metrics?query={urllib.parse.quote(json.dumps(query_dict))}"
        resp = requests.get(url, auth=auth)
        if resp.status_code == 200 and resp.json().get("data"):
            return resp.json()["data"][0]
        return {}
        
    # 1. Latency & Cost
    obs_query = {
        "view": "observations",
        "fromTimestamp": week_ago.isoformat(),
        "toTimestamp": now.isoformat(),
        "metrics": [
            { "measure": "latency", "aggregation": "p50" },
            { "measure": "latency", "aggregation": "p95" },
            { "measure": "totalCost", "aggregation": "sum" }
        ]
    }
    obs_data = fetch_metric(obs_query)
    
    # 2. Citation Coverage Score
    cov_query = {
        "view": "scores-numeric",
        "fromTimestamp": week_ago.isoformat(),
        "toTimestamp": now.isoformat(),
        "metrics": [
            { "measure": "value", "aggregation": "avg" }
        ],
        "filters": [
            { "type": "string", "column": "name", "operator": "=", "value": "citation_coverage" }
        ]
    }
    cov_data = fetch_metric(cov_query)
    
    # 3. Failure Score
    fail_query = {
        "view": "scores-numeric",
        "fromTimestamp": week_ago.isoformat(),
        "toTimestamp": now.isoformat(),
        "metrics": [
            { "measure": "value", "aggregation": "avg" }
        ],
        "filters": [
            { "type": "string", "column": "name", "operator": "=", "value": "failure" }
        ]
    }
    fail_data = fetch_metric(fail_query)
    
    result = {
        "p50_latency": obs_data.get("p50_latency", 0),
        "p95_latency": obs_data.get("p95_latency", 0),
        "total_cost": obs_data.get("sum_totalCost", 0),
        "citation_coverage": cov_data.get("avg_value", 0),
        "failure_rate": fail_data.get("avg_value", 0)
    }
    
    # Save to cache
    _METRICS_CACHE["data"] = result
    _METRICS_CACHE["timestamp"] = time.time()
    
    return result

# Mount the static files folder for the HTML UI page
# Checks if the static directory exists first
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    print(f"Warning: Static UI directory '{STATIC_DIR}' does not exist.")

def main():
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://localhost:{port}...")
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()
