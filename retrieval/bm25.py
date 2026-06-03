#!/usr/bin/env python3
import json
import os
import pickle
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

INDEX_PATH = Path(".bm25_index.pkl")
CHUNKS_PATH = Path("data/processed/chunks.json")

def tokenize(text: str) -> List[str]:
    """
    Cleans punctuation, lowercases, and splits text by whitespace.
    """
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    return cleaned.split()

class QuranBM25Index:
    def __init__(self, index_path: Path = INDEX_PATH, chunks_path: Path = CHUNKS_PATH):
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._load_or_build()

    def _load_or_build(self):
        if self.index_path.exists():
            print(f"Loading BM25 index from {self.index_path}...")
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.chunks = data["chunks"]
        else:
            print("BM25 index not found. Building index...")
            if not self.chunks_path.exists():
                print(f"Error: Chunks file missing at {self.chunks_path}. Run ingest/chunk.py first.")
                sys.exit(1)
                
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
                
            # Tokenize all chunks over English text + themes + tafsir_note
            corpus = []
            for c in self.chunks:
                text_to_index = c["text_english"]
                if c.get("tafsir_note"):
                    text_to_index += " " + c["tafsir_note"]
                corpus.append(tokenize(text_to_index))
                
            self.bm25 = BM25Okapi(corpus)
            
            # Save index to pickle
            with open(self.index_path, "wb") as f:
                pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
            print(f"BM25 index successfully saved to {self.index_path}")

    def search(self, query: str, n_results: int = 20) -> List[Dict[str, Any]]:
        """
        Tokenizes the query, scores all chunks, and returns the top n_results.
        Returns format: [{"chunk_id": "...", "metadata": {...}, "score": 12.34}]
        """
        if not self.bm25:
            return []
            
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Sort chunks by score in descending order
        ranked = sorted(
            zip(self.chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = []
        for chunk, score in ranked[:n_results]:
            # If the score is 0, we can stop or keep it (usually positive scores are keywords matches)
            if score <= 0.0:
                continue
                
            # Structure metadata matching the ChromaDB output format
            results.append({
                "chunk_id": chunk["chunk_id"],
                "document": chunk["text_english"],
                "metadata": {
                    "surah_number":    int(chunk["surah_number"]),
                    "surah_name_en":   str(chunk["surah_name_en"]),
                    "ayah_start":      int(chunk["ayah_start"]),
                    "ayah_end":        int(chunk["ayah_end"]),
                    "revelation_type": str(chunk["revelation_type"]),
                    "juz":             int(chunk["juz"]),
                    "chunk_type":      str(chunk["chunk_type"]),
                    "themes":          ",".join(chunk["themes"]) if isinstance(chunk["themes"], list) else str(chunk["themes"]),
                    "text_arabic":     str(chunk["text_arabic"]) if chunk["text_arabic"] else "",
                    "text_english":    str(chunk["text_english"]) if chunk["text_english"] else "",
                    "tafsir_note":     str(chunk["tafsir_note"]) if chunk.get("tafsir_note") else ""
                },
                "score": float(score)
            })
            
        return results

if __name__ == "__main__":
    print("=== BM25 Keyword Search Index ===")
    index = QuranBM25Index()
    
    # Test queries
    test_queries = ["riba", "patience", "how to pray"]
    for q in test_queries:
        print(f"\nSearching for keyword: '{q}'")
        res = index.search(q, n_results=3)
        for idx, r in enumerate(res):
            print(f"  [{idx+1}] ID: {r['chunk_id']} | BM25 Score: {r['score']:.4f}")
            print(f"    English: {r['metadata']['text_english'][:120]}...")
