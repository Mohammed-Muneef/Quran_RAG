#!/usr/bin/env python3
import os
import sys
import time
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
from langfuse import observe

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
        
        return AskResponse(
            answer=clean_summary,
            verses=citation_list,
            disclaimer="For a ruling specific to your situation, consult a qualified scholar (alim).",
            retrieval_time_ms=elapsed_ms
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
