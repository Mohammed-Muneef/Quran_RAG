#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import chromadb
try:
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
except ImportError:
    SentenceTransformerEmbeddingFunction = None  # Not available in lightweight deployments
from chromadb import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        from google import genai

        self.client = genai.Client(api_key=api_key)

        # Retry settings
        self.max_retries = 8
        self.base_delay = 2
        self.max_delay = 60

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings with exponential backoff.

        Retries:
        - 429 RESOURCE_EXHAUSTED
        - 500 Internal errors
        - 502 Bad Gateway
        - 503 Service Unavailable
        - 504 Gateway Timeout
        """

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=input,
                )

                if hasattr(response, "embeddings"):
                    return [emb.values for emb in response.embeddings]

                elif isinstance(response, list):
                    return [emb.values for emb in response]

                else:
                    raise ValueError(
                        f"Unexpected Gemini response structure: {type(response)}"
                    )

            except Exception as e:
                error_str = str(e)

                retryable = any(
                    code in error_str
                    for code in [
                        "429",
                        "RESOURCE_EXHAUSTED",
                        "500",
                        "502",
                        "503",
                        "504",
                    ]
                )

                if not retryable:
                    print(f"Non-retryable Gemini error: {e}")
                    raise

                if attempt == self.max_retries - 1:
                    print(
                        f"Gemini embedding failed after "
                        f"{self.max_retries} attempts"
                    )
                    raise

                # Exponential backoff
                delay = min(
                    self.base_delay * (2 ** attempt),
                    self.max_delay,
                )

                # Add jitter
                jitter = random.uniform(0, 1)
                sleep_time = delay + jitter

                print(
                    f"[Retry {attempt + 1}/{self.max_retries}] "
                    f"Gemini rate limit/server error. "
                    f"Sleeping {sleep_time:.2f}s..."
                )

                time.sleep(sleep_time)

        raise RuntimeError(
            "Failed to generate embeddings after all retries."
        )

class QuranChromaStore:
    def __init__(self, db_path: str = ".chroma", collection_name: str = "quran_verses"):
        """
        Initializes persistent ChromaDB store at db_path and retrieves/creates the collection.
        Defaults to local sentence-transformers 'all-MiniLM-L6-v2' to avoid bulk rate limits,
        but dynamically supports Gemini gemini-embedding-001 if USE_GEMINI_EMBEDDINGS=true is set
        or if sentence-transformers is not installed.
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        use_gemini = os.environ.get("USE_GEMINI_EMBEDDINGS", "false").lower() == "true"
        
        # Check if sentence-transformers is available
        import importlib.util
        st_available = importlib.util.find_spec("sentence_transformers") is not None
        if st_available:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        
        # Auto-use Gemini if sentence-transformers is not installed
        if not st_available and gemini_key:
            use_gemini = True
        
        if use_gemini and gemini_key:
            print("Using Gemini Embedding Function (gemini-embedding-001)...")
            self.embedding_function = GeminiEmbeddingFunction(api_key=gemini_key)
            if collection_name == "quran_verses":
                collection_name = "quran_verses_gemini"
        elif st_available:
            print("Using Local Embedding Function (all-MiniLM-L6-v2)...")
            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            raise RuntimeError(
                "No embedding function available. Either:\n"
                "  1. Install sentence-transformers: pip install sentence-transformers\n"
                "  2. Set GEMINI_API_KEY environment variable to use Gemini embeddings"
            )
            
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def upsert_chunks(self, chunks: List[Dict[str, Any]], progress_interval: int = 500):
        """
        Embeds each chunk's (text_english + tafsir_note) and stores with full metadata.
        Prints progress every `progress_interval` chunks.
        """
        total_chunks = len(chunks)
        print(f"Upserting {total_chunks:,} chunks to ChromaDB...")
        
        batch_size = 100
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            
            ids = [c["chunk_id"] for c in batch]
            # Embed the English translation and Tafsir note combined
            documents = []
            for c in batch:
                text_to_embed = c["text_english"]
                if c.get("tafsir_note"):
                    text_to_embed += " " + c["tafsir_note"]
                documents.append(text_to_embed)
                
            metadatas = []
            for c in batch:
                meta = {
                    "surah_number":    int(c["surah_number"]),
                    "surah_name_en":   str(c["surah_name_en"]),
                    "ayah_start":      int(c["ayah_start"]),
                    "ayah_end":        int(c["ayah_end"]),
                    "revelation_type": str(c["revelation_type"]),
                    "juz":             int(c["juz"]),
                    "chunk_type":      str(c["chunk_type"]),
                    "themes":          ",".join(c["themes"]) if isinstance(c["themes"], list) else str(c["themes"]),
                    "text_arabic":     str(c["text_arabic"]) if c["text_arabic"] else "",
                    "text_english":    str(c["text_english"]) if c["text_english"] else "",
                    "tafsir_note":     str(c["tafsir_note"]) if c.get("tafsir_note") else ""
                }
                metadatas.append(meta)
                
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            # Print progress
            completed = min(i + batch_size, total_chunks)
            if completed % progress_interval == 0 or completed == total_chunks:
                print(f"  Processed {completed}/{total_chunks} chunks...")
                
        print(f"Upsert complete. Collection size: {self.collection.count()}")

    def similarity_search(self, query: str, n_results: int = 10, filters: Optional[dict] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic search against ChromaDB.
        `filters` can be passed as a dictionary matching ChromaDB query filters (e.g. {"surah_number": 2})
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )
        
        formatted_results = []
        if not results or not results["ids"] or len(results["ids"][0]) == 0:
            return formatted_results
            
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
        
        for idx in range(len(ids)):
            formatted_results.append({
                "chunk_id": ids[idx],
                "document": documents[idx],
                "metadata": metadatas[idx],
                "distance": distances[idx]
            })
            
        return formatted_results

if __name__ == "__main__":
    print("=== ChromaDB Ingestion ===")
    chunks_path = Path("data/processed/chunks.json")
    if not chunks_path.exists():
        print("Error: chunks.json not found. Run ingest/chunk.py first.")
        sys.exit(1)
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    store = QuranChromaStore()
    
    # Run upsert
    store.upsert_chunks(chunks)
    
    # Run test search
    print("\nRunning test semantic query for 'riba'...")
    results = store.similarity_search("interest and riba", n_results=2)
    for idx, r in enumerate(results):
        print(f"[{idx+1}] ID: {r['chunk_id']} | Distance: {r['distance']:.4f}")
        print(f"  English: {r['metadata']['text_english'][:120]}...")
