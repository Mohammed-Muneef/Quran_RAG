#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any

# Target cache path
CACHE_PATH = Path(".expand_cache.json")

EXPANSION_SYSTEM_PROMPT = """You are a helpful assistant that expands English search queries about the Quran.
Your goal is to extract relevant Arabic Islamic terms, related Quranic concepts, and modern English synonyms to bridge the vocabulary gap.

Extract:
1. Transliterated Arabic Islamic terms (e.g., interest -> riba, prayer -> salah, charity -> zakat, fasting -> sawm/ramadan, pilgrimage -> hajj, forbidden -> haram, lawful -> halal).
2. Modern English synonyms or related terms.
3. Quranic concepts.

Combine all of these terms into a single, clean, space-separated string containing the original query terms plus the new search terms.
Do not add any conversational filler, markdown, bullet points, or explanations. Only return the final space-separated expanded query.

Examples:
- Input: "is interest haram" -> Output: "is interest haram riba usury lending debt forbidden"
- Input: "how many times to pray" -> Output: "how many times to pray salah prayer prostration bow worship"
- Input: "rules of marriage and divorce" -> Output: "rules of marriage and divorce nikah talaq iddah spouse family husband wife separation"
"""

def get_query_hash(query: str) -> str:
    return hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()

def load_cache() -> Dict[str, str]:
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, str]):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save query expansion cache: {e}")

def expand_query(query: str) -> str:
    """
    Expands the user query using the Gemini API or OpenAI API depending on available keys.
    Caches the results locally in .expand_cache.json.
    """
    clean_query = query.strip()
    if not clean_query:
        return ""

    query_hash = get_query_hash(clean_query)
    cache = load_cache()
    
    if query_hash in cache:
        return cache[query_hash]

    # Check for keys in environment
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    expanded = clean_query

    # Try Gemini API first
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            print(f"Expanding query '{clean_query}' using Gemini...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Input question: \"{clean_query}\"\nOutput:",
                config={
                    "system_instruction": EXPANSION_SYSTEM_PROMPT,
                    "temperature": 0.1
                }
            )
            expanded = response.text.strip()
        except Exception as e:
            print(f"Gemini expansion failed: {e}. Trying OpenAI fallback...")
            
    # Try OpenAI fallback if Gemini key is missing or failed
    if expanded == clean_query and openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            print(f"Expanding query '{clean_query}' using OpenAI...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": EXPANSION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Input question: \"{clean_query}\""}
                ],
                temperature=0.1
            )
            expanded = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI expansion failed: {e}")

    # Fallback to local heuristic mapping if no API keys are available
    if expanded == clean_query:
        # Simple local dictionary of common expansions
        local_mapping = {
            "interest": "interest riba usury debt lending finance",
            "riba": "riba interest usury debt lending finance",
            "pray": "pray prayer salah prostrate bow worship namaz",
            "salah": "salah prayer prostrate bow worship namaz",
            "charity": "charity zakat alms sadakah poor-due giving",
            "zakat": "zakat charity alms sadakah poor-due giving",
            "fasting": "fasting sawm ramadan fasting rules iftar",
            "sawm": "sawm fasting ramadan fasting rules iftar",
            "pork": "pork pig swine meat forbidden food haram",
            "marriage": "marriage nikah wedding spouse husband wife family",
            "divorce": "divorce talaq iddah separation husband wife family",
            "patience": "patience sabr steadfast persevere endurance trials"
        }
        
        words = clean_query.lower().split()
        expansions = []
        for word in words:
            # strip non-alphanumeric
            word_clean = "".join(ch for ch in word if ch.isalnum())
            if word_clean in local_mapping:
                expansions.append(local_mapping[word_clean])
                
        if expansions:
            # Combine original and mapped words, keeping unique terms
            combined_terms = clean_query.split() + " ".join(expansions).split()
            seen = set()
            unique_terms = [t for t in combined_terms if not (t.lower() in seen or seen.add(t.lower()))]
            expanded = " ".join(unique_terms)
            print(f"Mock query expansion (local rule): '{clean_query}' -> '{expanded}'")
        else:
            print(f"No API key and no local mapping found. Using original query: '{clean_query}'")

    # Cache result if it changed
    if expanded != clean_query:
        cache[query_hash] = expanded
        save_cache(cache)

    return expanded

if __name__ == "__main__":
    print("=== Query Expansion Tester ===")
    test_queries = [
        "is interest haram",
        "can I eat pork",
        "how many times to pray"
    ]
    for q in test_queries:
        res = expand_query(q)
        print(f"Query: '{q}'\n  Expanded: '{res}'")
        print("-" * 50)
