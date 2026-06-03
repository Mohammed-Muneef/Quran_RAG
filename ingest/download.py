#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
import requests

# Constants
TANZIL_ARABIC_URL = "https://tanzil.net/pub/download/index.php"
TANZIL_ARABIC_DATA = {"quranType": "uthmani", "outType": "txt-2"}
TANZIL_ENGLISH_URL = "https://tanzil.net/trans/"
TANZIL_ENGLISH_PARAMS = {"transID": "en.sahih", "type": "txt-2"}

ALQURAN_ARABIC_URL = "https://api.alquran.cloud/v1/quran/quran-uthmani"
ALQURAN_ENGLISH_URL = "https://api.alquran.cloud/v1/quran/en.sahih"

RAW_DIR = Path("data/raw")
RAW_ARABIC_FILE = RAW_DIR / "quran_arabic.json"
RAW_ENGLISH_FILE = RAW_DIR / "quran_english.json"

def parse_tanzil_txt(text: str) -> dict[str, str]:
    """
    Tanzil format lines: surah|ayah|verse_text
    Returns dictionary mapping "surah:ayah" -> "verse_text"
    """
    verses = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            surah, ayah, text_val = parts
            verses[f"{surah}:{ayah}"] = text_val.strip()
    return verses

def fetch_from_tanzil_arabic() -> dict[str, str]:
    print("Fetching Arabic text from tanzil.net...")
    r = requests.post(TANZIL_ARABIC_URL, data=TANZIL_ARABIC_DATA, timeout=30)
    r.raise_for_status()
    raw_text = r.content.decode("utf-8-sig")
    return parse_tanzil_txt(raw_text)

def fetch_from_tanzil_english() -> dict[str, str]:
    print("Fetching English text from tanzil.net...")
    r = requests.get(TANZIL_ENGLISH_URL, params=TANZIL_ENGLISH_PARAMS, timeout=30)
    r.raise_for_status()
    raw_text = r.content.decode("utf-8-sig")
    return parse_tanzil_txt(raw_text)

def fetch_from_alquran_api(url: str, label: str) -> dict[str, str]:
    print(f"Fallback: Fetching {label} from alquran.cloud API...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    
    verses = {}
    surahs = data.get("data", {}).get("surahs", [])
    
    for s_idx, surah in enumerate(surahs):
        surah_num = surah["number"]
        # Print progress every 10 surahs
        if s_idx % 10 == 0:
            print(f"  Processed {s_idx}/{len(surahs)} surahs for {label}...")
            
        for ayah in surah["ayahs"]:
            key = f"{surah_num}:{ayah['numberInSurah']}"
            verses[key] = ayah["text"].strip()
            
    print(f"  → {len(verses):,} verses loaded for {label}")
    return verses

def download_corpus():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Download Arabic Uthmani Text
    if RAW_ARABIC_FILE.exists():
        print(f"Arabic corpus already exists at {RAW_ARABIC_FILE}. Skipping download.")
    else:
        try:
            arabic_data = fetch_from_tanzil_arabic()
            if not arabic_data:
                raise ValueError("Parsed tanzil data is empty.")
            print(f"Successfully loaded {len(arabic_data):,} Arabic verses from tanzil.net")
        except Exception as e:
            print(f"Tanzil.net Arabic download failed: {e}")
            try:
                arabic_data = fetch_from_alquran_api(ALQURAN_ARABIC_URL, "Arabic")
            except Exception as ex:
                print(f"Fallback AlQuran API Arabic download failed: {ex}")
                sys.exit(1)
                
        with open(RAW_ARABIC_FILE, "w", encoding="utf-8") as f:
            json.dump(arabic_data, f, ensure_ascii=False, indent=2)
        print(f"Saved raw Arabic JSON to {RAW_ARABIC_FILE}")

    # 2. Download English Sahih International Text
    if RAW_ENGLISH_FILE.exists():
        print(f"English corpus already exists at {RAW_ENGLISH_FILE}. Skipping download.")
    else:
        try:
            english_data = fetch_from_tanzil_english()
            if not english_data:
                raise ValueError("Parsed tanzil data is empty.")
            print(f"Successfully loaded {len(english_data):,} English verses from tanzil.net")
        except Exception as e:
            print(f"Tanzil.net English download failed: {e}")
            try:
                english_data = fetch_from_alquran_api(ALQURAN_ENGLISH_URL, "English")
            except Exception as ex:
                print(f"Fallback AlQuran API English download failed: {ex}")
                sys.exit(1)

        with open(RAW_ENGLISH_FILE, "w", encoding="utf-8") as f:
            json.dump(english_data, f, ensure_ascii=False, indent=2)
        print(f"Saved raw English JSON to {RAW_ENGLISH_FILE}")

if __name__ == "__main__":
    print("=== Quran Corpus Download Script ===")
    download_corpus()
