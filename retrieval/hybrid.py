#!/usr/bin/env python3
import concurrent.futures
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from retrieval.bm25 import QuranBM25Index
from retrieval.vector import QuranVectorSearch
from retrieval.expand import expand_query
from langfuse import observe

class QuranHybridSearch:
    def __init__(self):
        self.bm25_index = QuranBM25Index()
        self.vector_search = QuranVectorSearch()

    @observe()
    def search(self, query: str, n_results: int = 20, surah_number: Optional[int] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Runs query expansion and performs parallel BM25 and Vector search,
        then merges and ranks results using Reciprocal Rank Fusion (RRF)
        with keyword boosting.
        
        Returns:
            Tuple of (fused_results, expanded_query)
        """
        # 1. Expand query
        expanded_query = expand_query(query)
        
        # Setup filters for Vector search
        filters = None
        if surah_number is not None:
            filters = {"surah_number": int(surah_number)}

        # 2. Run searches in parallel
        # We retrieve 50 candidates from each to ensure rich RRF coverage
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_bm25 = executor.submit(self.bm25_index.search, expanded_query, n_results=50)
            future_vector = executor.submit(self.vector_search.search, expanded_query, n_results=50, filters=filters)
            
            bm25_results = future_bm25.result()
            vector_results = future_vector.result()

        # Apply Surah filtering on BM25 results locally (BM25 doesn't natively filter metadata)
        if surah_number is not None:
            bm25_results = [r for r in bm25_results if r["metadata"]["surah_number"] == surah_number]

        # 3. Reciprocal Rank Fusion (RRF), k = 60
        rrf_scores = {}
        chunks_cache = {}
        k = 60
        
        # Merge BM25 ranks
        for rank, res in enumerate(bm25_results, 1):
            cid = res["chunk_id"]
            chunks_cache[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank)
            
        # Merge Vector ranks
        for rank, res in enumerate(vector_results, 1):
            cid = res["chunk_id"]
            chunks_cache[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank)

        # 4. Keyword Boost: uplift chunks whose themes/tafsir match expanded query terms
        expanded_terms = set(re.sub(r'[^\w\s]', '', expanded_query.lower()).split())
        # Remove common stopwords from boost terms
        stopwords = {"is", "a", "the", "an", "and", "or", "in", "on", "of", "to", "it", "do", "we", "i", "how", "what", "are", "can", "does"}
        boost_terms = expanded_terms - stopwords
        
        KEYWORD_BOOST = 0.01  # Small enough to influence ranking without overwhelming RRF
        for cid, chunk_data in chunks_cache.items():
            meta = chunk_data.get("metadata", {})
            # Combine themes + tafsir_note for matching
            themes_text = meta.get("themes", "").lower()
            tafsir_text = meta.get("tafsir_note", "").lower()
            english_text = meta.get("text_english", "").lower()
            searchable = f"{themes_text} {tafsir_text} {english_text}"
            
            match_count = sum(1 for term in boost_terms if term in searchable)
            if match_count > 0:
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + KEYWORD_BOOST * match_count

        # 5. Sort and filter top results by RRF score
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        fused_results = []
        for cid, score in sorted_rrf[:n_results]:
            chunk_data = chunks_cache[cid]
            res_copy = dict(chunk_data)
            res_copy["rrf_score"] = float(score)
            fused_results.append(res_copy)
            
        return fused_results, expanded_query

def print_comparison(bm25: list, vector: list, hybrid: list):
    print("=" * 100)
    print(f"{'BM25 (Keyword)':<30} | {'Vector (Semantic)':<30} | {'Hybrid (RRF + Expansion)':<30}")
    print("=" * 100)
    
    max_len = max(len(bm25), len(vector), len(hybrid))
    for i in range(min(max_len, 5)):
        b_ref = bm25[i]["chunk_id"] if i < len(bm25) else "-"
        v_ref = vector[i]["chunk_id"] if i < len(vector) else "-"
        h_ref = hybrid[i]["chunk_id"] if i < len(hybrid) else "-"
        
        b_text = bm25[i]["metadata"]["text_english"][:25] + "..." if i < len(bm25) else "-"
        v_text = vector[i]["metadata"]["text_english"][:25] + "..." if i < len(vector) else "-"
        h_text = hybrid[i]["metadata"]["text_english"][:25] + "..." if i < len(hybrid) else "-"
        
        print(f"{b_ref:<6} {b_text:<23} | {v_ref:<6} {v_text:<23} | {h_ref:<6} {h_text:<23}")
    print("=" * 100)

if __name__ == "__main__":
    print("=== Hybrid Retrieval Tester ===")
    searcher = QuranHybridSearch()
    
    test_query = "is loan haram?"
    
    print(f"Comparing retrieval mechanisms for query: '{test_query}'\n")
    
    # 1. BM25 Only (unexpanded)
    bm25_results = searcher.bm25_index.search(test_query, n_results=5)
    
    # 2. Vector Only (unexpanded)
    vector_results = searcher.vector_search.search(test_query, n_results=5)
    
    # 3. Hybrid (RRF + expanded + keyword boost)
    hybrid_results, expanded = searcher.search(test_query, n_results=5)
    
    print(f"Expanded query: '{expanded}'\n")
    print_comparison(bm25_results, vector_results, hybrid_results)
    
    # Print the top hybrid chunk details
    if hybrid_results:
        top = hybrid_results[0]
        meta = top["metadata"]
        print(f"\nTop Hybrid Chunk: {top['chunk_id']} | Surah: {meta['surah_name_en']} | RRF Score: {top['rrf_score']:.4f}")
        print(f"  Arabic: {meta['text_arabic']}")
        print(f"  English: {meta['text_english']}")
