#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from store.chroma_store import QuranChromaStore

class QuranVectorSearch:
    def __init__(self, db_path: str = ".chroma", collection_name: str = "quran_verses"):
        self.store = QuranChromaStore(db_path=db_path, collection_name=collection_name)

    def search(self, query: str, n_results: int = 10, filters: Optional[dict] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search against the ChromaDB collection.
        """
        return self.store.similarity_search(query, n_results=n_results, filters=filters)

def main():
    parser = argparse.ArgumentParser(description="Quranic Vector Search & Cited QA CLI")
    parser.add_argument("query", type=str, help="Semantic search query")
    parser.add_argument("--surah", type=int, default=None, help="Optional Surah number to filter by")
    parser.add_argument("--top_k", type=int, default=5, help="Number of chunks to retrieve (default: 5)")
    args = parser.parse_args()

    print(f"Searching for: '{args.query}'...")
    searcher = QuranVectorSearch()
    
    # Setup Chroma filters
    filters = None
    if args.surah:
        filters = {"surah_number": args.surah}
        
    chunks = searcher.search(args.query, n_results=args.top_k, filters=filters)
    
    if not chunks:
        print("No matching Quranic verses found in vector store.")
        sys.exit(0)
        
    print(f"\nRetrieved {len(chunks)} matching chunks:")
    for idx, c in enumerate(chunks):
        meta = c["metadata"]
        cosine_sim = 1.0 - c["distance"]
        print(f"  [{idx+1}] ID: {c['chunk_id']} | Surah: {meta['surah_name_en']} ({meta['surah_number']}:{meta['ayah_start']}-{meta['ayah_end']}) | Sim: {cosine_sim:.4f}")
        print(f"    Arabic: {meta['text_arabic'][:80]}...")
        print(f"    English: {meta['text_english'][:120]}...")
        print("-" * 50)

    # Lazy import to avoid circular dependency
    try:
        from generation.answer import generate_answer
    except ImportError:
        print("\nNote: Generation module 'generation.answer' not yet implemented.")
        return

    print("\nGenerating cited answer...")
    result = generate_answer(args.query, chunks)
    
    print("\n=== CITED ANSWER ===")
    print(result.get("answer"))
    print("\n=== CITATIONS ===")
    for cit in result.get("citations", []):
        print(f"- {cit['surah']} ({cit['ayah']})")
        print(f"  English: {cit['text_en']}")
        print(f"  Arabic: {cit['text_ar']}")

if __name__ == "__main__":
    main()
