#!/usr/bin/env python3
import json
from pathlib import Path

# Theme keywords map for tagging themes dynamically in chunk.py
THEME_MAP = {
    "riba":         ["riba", "interest", "usury", "loan", "debt", "creditor"],
    "zakat":        ["zakat", "alms", "charity", "poor due", "purification"],
    "salah":        ["prayer", "salah", "prostrate", "bow", "worship", "qibla"],
    "sawm":         ["fasting", "ramadan", "sawm", "iftar", "suhoor"],
    "hajj":         ["hajj", "pilgrimage", "mecca", "kaaba", "ihram"],
    "marriage":     ["marriage", "nikah", "spouse", "husband", "wife", "dowry"],
    "divorce":      ["divorce", "talaq", "iddah", "separation"],
    "halal_haram":  ["forbidden", "prohibited", "lawful", "unlawful", "haram", "halal"],
    "justice":      ["justice", "equity", "oppression", "witness", "testimony"],
    "patience":     ["patience", "sabr", "steadfast", "persevere", "trials"],
    "afterlife":    ["paradise", "hellfire", "resurrection", "judgment", "akhira"],
    "tawhid":       ["monotheism", "oneness", "shirk", "polytheism", "god alone"],
}

def detect_themes(text_english: str) -> list[str]:
    text_lower = text_english.lower()
    themes = []
    for theme, keywords in THEME_MAP.items():
        if any(kw in text_lower for kw in keywords):
            themes.append(theme)
    return themes

def group_consecutive_indices(verses: list[dict], theme: str) -> list[list[dict]]:
    """
    Finds contiguous runs of verses in a Surah that share the same theme.
    """
    runs = []
    current_run = []
    
    for v in verses:
        if theme in v["themes"]:
            if not current_run or v["ayah_number"] == current_run[-1]["ayah_number"] + 1:
                current_run.append(v)
            else:
                if len(current_run) >= 2:
                    runs.append(current_run)
                current_run = [v]
        else:
            if len(current_run) >= 2:
                runs.append(current_run)
            current_run = []
            
    if len(current_run) >= 2:
        runs.append(current_run)
    return runs

def slide_window_on_run(run: list[dict], min_size: int = 3, max_size: int = 5, overlap: int = 1) -> list[list[dict]]:
    """
    Slides a window of size min_size to max_size with an overlap of 'overlap' over a run of verses.
    """
    windows = []
    n = len(run)
    if n < min_size:
        # If the run is too small for a sliding window (e.g. 2 verses), we still keep it as a thematic chunk
        return [run]
        
    start = 0
    while start < n:
        end = start + max_size
        if end > n:
            end = n
        
        # If the remaining slice is smaller than min_size, merge it with the last window or expand backward
        if (end - start) < min_size and len(windows) > 0:
            # Shift start backward to form a full window size of max_size ending at the end of the run
            start = max(0, end - max_size)
            window = run[start:end]
            if window not in windows:
                windows.append(window)
            break
            
        windows.append(run[start:end])
        start = end - overlap
        if start >= n - 1:
            break
            
    return windows

def chunk_corpus():
    merged_path = Path("data/processed/quran_merged.json")
    processed_dir = Path("data/processed")
    chunks_output_path = processed_dir / "chunks.json"

    if not merged_path.exists():
        print("Error: Merged file missing. Run merge.py first.")
        return

    print("Loading merged corpus...")
    with open(merged_path, "r", encoding="utf-8") as f:
        merged_verses = json.load(f)

    # 1. Detect themes and store them in the database list
    print("Detecting themes for all verses...")
    for v in merged_verses:
        v["themes"] = detect_themes(v["text_english"])

    # Group verses by Surah
    surah_groups = {}
    for v in merged_verses:
        surah_groups.setdefault(v["surah_number"], []).append(v)

    chunks = []
    used_ids_per_surah = {} # Keeps track of single verses to verify no redundancy if needed, but the prompt requests:
    # "Creates chunks at the ayah level — one chunk per verse AND also creates thematic group chunks"
    # So every verse will have a single-ayah chunk, and we will ALSO have thematic chunks. This represents full coverage.

    # 2. Build Single-Ayah Chunks (for all verses)
    print("Building single-ayah chunks...")
    for v in merged_verses:
        chunks.append({
            "chunk_id": f"{v['surah_number']}:{v['ayah_number']}",
            "chunk_type": "single",
            "surah_number": v["surah_number"],
            "surah_name_en": v["surah_name_en"],
            "ayah_start": v["ayah_number"],
            "ayah_end": v["ayah_number"],
            "text_arabic": v["text_arabic"],
            "text_english": v["text_english"],
            "themes": v["themes"],
            "revelation_type": v["revelation_type"],
            "juz": v["juz"],
            "tafsir_note": ""
        })

    # 3. Build Thematic Group Chunks
    print("Building thematic group chunks...")
    total_thematic_chunks = 0
    for surah_num, verses in sorted(surah_groups.items()):
        # Sort verses in Surah
        verses = sorted(verses, key=lambda x: x["ayah_number"])
        
        # Check each possible theme
        for theme in THEME_MAP.keys():
            runs = group_consecutive_indices(verses, theme)
            for run in runs:
                # Apply sliding window of 3-5 verses with overlap of 1
                windows = slide_window_on_run(run, min_size=3, max_size=5, overlap=1)
                for w in windows:
                    start_ayah = w[0]["ayah_number"]
                    end_ayah = w[-1]["ayah_number"]
                    
                    # Merge content
                    arabic_joined = " ۝ ".join(v["text_arabic"] for v in w)
                    english_joined = " ".join(v["text_english"] for v in w)
                    
                    chunks.append({
                        "chunk_id": f"{surah_num}:{start_ayah}-{end_ayah}-{theme}",
                        "chunk_type": "thematic",
                        "surah_number": surah_num,
                        "surah_name_en": w[0]["surah_name_en"],
                        "ayah_start": start_ayah,
                        "ayah_end": end_ayah,
                        "text_arabic": arabic_joined,
                        "text_english": english_joined,
                        "themes": [theme],
                        "revelation_type": w[0]["revelation_type"],
                        "juz": w[0]["juz"],
                        "tafsir_note": ""
                    })
                    total_thematic_chunks += 1


    with open(chunks_output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    print(f"Saved total of {len(chunks):,} chunks to {chunks_output_path}")
    print(f"  → Single-ayah chunks: {len(merged_verses):,}")
    print(f"  → Thematic sliding-window chunks: {total_thematic_chunks:,}")

if __name__ == "__main__":
    chunk_corpus()
