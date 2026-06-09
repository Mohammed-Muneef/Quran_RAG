#!/usr/bin/env python3
import json
import os
import re
import sys
from typing import List, Dict, Any
from langfuse import observe

# Lazy-loaded imports for performance
_cohere_client = None
_cross_encoder = None

def get_cohere_client(api_key: str):
    global _cohere_client
    if _cohere_client is None:
        import cohere
        _cohere_client = cohere.Client(api_key=api_key)
    return _cohere_client

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        print("Loading local CrossEncoder ('cross-encoder/ms-marco-MiniLM-L-6-v2')...")
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder

def _build_candidate_text(candidate: Dict[str, Any]) -> str:
    """Extract combined English text + tafsir for a candidate chunk."""
    text = candidate["metadata"]["text_english"]
    if candidate["metadata"].get("tafsir_note"):
        text += " " + candidate["metadata"]["tafsir_note"]
    return text


@observe(as_type="generation")
def _gemini_rerank(query: str, candidates: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    """
    Uses Gemini to score each candidate's relevance to the query.
    Sends all candidates in a single API call for efficiency.
    Returns sorted list with rerank_score field.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not gemini_key:
        return []

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
    except ImportError:
        print("google-genai not installed, skipping Gemini reranking.")
        return []

    # Build the prompt with all candidates
    candidate_texts = []
    for idx, c in enumerate(candidates):
        text = _build_candidate_text(c)
        candidate_texts.append(f"[{idx}] {c['chunk_id']}: {text[:300]}")

    candidates_block = "\n".join(candidate_texts)

    prompt = f"""You are a Quranic relevance scorer. Given a user's question about Islam and a list of Quranic verse chunks, score each chunk's relevance to the question on a scale of 0-10.

Scoring guidelines:
- 10: Directly answers the question with the exact Quranic ruling or concept
- 7-9: Highly relevant, addresses the core topic
- 4-6: Somewhat related but not the primary answer
- 1-3: Tangentially related
- 0: Completely irrelevant

IMPORTANT: Understand Islamic terminology. For example:
- "riba" = interest/usury (financial), NOT "goodly loan to Allah" (metaphorical)
- "loan" in financial context refers to borrowing money, not "lending to Allah" which means giving charity
- "haram" = forbidden/prohibited

User Question: "{query}"

Candidate Chunks:
{candidates_block}

Return ONLY a JSON array of objects with "index" (integer) and "score" (float 0-10) for each chunk, sorted by score descending. No explanation.
Example: [{{"index": 2, "score": 9.5}}, {{"index": 0, "score": 3.0}}]"""

    try:
        print("Reranking candidates using Gemini...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json"
            }
        )
        raw = response.text.strip()
        scores = json.loads(raw)

        # Map scores back to candidates
        reranked = []
        for entry in scores:
            idx = int(entry["index"])
            score = float(entry["score"])
            if 0 <= idx < len(candidates):
                c_copy = dict(candidates[idx])
                c_copy["rerank_score"] = score
                reranked.append(c_copy)

        # Sort by score descending and take top_n
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_n]

    except Exception as e:
        print(f"Gemini reranking failed: {e}")
        return []


@observe()
def rerank_chunks(query: str, candidates: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Reranks up to 20 candidate chunks using (in priority order):
    1. Gemini API (best for Islamic domain understanding)
    2. Cohere Rerank API (rerank-english-v3.0)
    3. Local CrossEncoder (ms-marco-MiniLM-L-6-v2) as final fallback
    """
    if not candidates:
        return []

    # Max candidates to rerank is 20
    candidates = candidates[:20]

    # --- Priority 1: Gemini Reranking ---
    reranked_results = _gemini_rerank(query, candidates, top_n)
    if reranked_results:
        _log_reranked(reranked_results, method="Gemini")
        return reranked_results

    # --- Priority 2: Cohere Rerank ---
    cohere_key = os.environ.get("COHERE_API_KEY")
    if cohere_key:
        try:
            print("Reranking candidates using Cohere API...")
            co = get_cohere_client(cohere_key)
            
            documents = [_build_candidate_text(c) for c in candidates]
                
            response = co.rerank(
                model='rerank-english-v3.0',
                query=query,
                documents=documents,
                top_n=top_n
            )
            
            reranked_results = []
            for result in response.results:
                idx = result.index
                c_copy = dict(candidates[idx])
                c_copy["rerank_score"] = float(result.relevance_score)
                reranked_results.append(c_copy)

            _log_reranked(reranked_results, method="Cohere")
            return reranked_results
                
        except Exception as e:
            print(f"Cohere Rerank API failed: {e}. Falling back to local CrossEncoder...")

    # --- Priority 3: Local CrossEncoder ---
    try:
        print("Reranking candidates using local CrossEncoder...")
        encoder = get_cross_encoder()
        
        pairs = [[query, _build_candidate_text(c)] for c in candidates]
            
        scores = encoder.predict(pairs)
        
        ranked_pairs = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        reranked_results = []
        for candidate, score in ranked_pairs[:top_n]:
            c_copy = dict(candidate)
            c_copy["rerank_score"] = float(score)
            reranked_results.append(c_copy)

        _log_reranked(reranked_results, method="CrossEncoder")
        return reranked_results
            
    except Exception as e:
        print(f"Local CrossEncoder failed: {e}. Returning raw sorted candidates...")
        reranked_results = []
        for c in candidates[:top_n]:
            c_copy = dict(c)
            c_copy["rerank_score"] = 0.0
            reranked_results.append(c_copy)
        _log_reranked(reranked_results, method="Fallback")
        return reranked_results


def _log_reranked(results: List[Dict[str, Any]], method: str = ""):
    """Log reranked chunk scores for debugging."""
    print(f"Reranked Top Chunks ({method}):")
    for idx, r in enumerate(results):
        print(f"  [{idx+1}] Chunk: {r['chunk_id']} | Rerank Score: {r['rerank_score']:.4f}")

if __name__ == "__main__":
    print("=== Reranker Tester ===")
    from retrieval.hybrid import QuranHybridSearch
    
    hybrid_search = QuranHybridSearch()
    query = "is charging interest allowed"
    
    # Retrieve top 20 candidates
    print(f"Retrieving top candidates for query: '{query}'...")
    candidates = hybrid_search.search(query, n_results=20)
    
    # Rerank candidates
    top_5 = rerank_chunks(query, candidates, top_n=5)
    print(f"\nSuccessfully reranked to top {len(top_5)} candidates.")
