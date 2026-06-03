#!/usr/bin/env python3
import re
from typing import List, Set, Dict, Any

# Total verses per Surah in the Quran (114 Surahs)
SURAH_VERSE_COUNTS = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109,
    11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135,
    21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
    31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85,
    41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
    51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
    61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
    71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42,
    81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20,
    91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
    101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
    111: 5, 112: 4, 113: 5, 114: 6
}

def parse_verses_from_text(text: str) -> Set[str]:
    """
    Parses verse references like "2:275" or "2:275-280" from a text string.
    Returns a set of normalized verse references.
    """
    # Regex matching surah:ayah (and optionally -ayah for ranges)
    pattern = r'\b(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?\b'
    matches = re.findall(pattern, text)
    
    parsed_refs = set()
    for m in matches:
        surah, start_ayah, end_ayah = m
        surah_num = int(surah)
        start_num = int(start_ayah)
        
        if end_ayah:
            end_num = int(end_ayah)
            # Expand range to individual verses
            for a in range(start_num, end_num + 1):
                parsed_refs.add(f"{surah_num}:{a}")
        else:
            parsed_refs.add(f"{surah_num}:{start_num}")
            
    return parsed_refs

def parse_expected_verses(expected_list: List[str]) -> Set[str]:
    """
    Normalizes expected references to individual verse keys (e.g. "2:275-276" -> {"2:275", "2:276"}).
    """
    normalized = set()
    for item in expected_list:
        # Check if it has a hyphen range
        if "-" in item:
            ref_part, end_part = item.split("-")
            surah, start_ayah = ref_part.split(":")
            surah_num = int(surah)
            start_num = int(start_ayah)
            end_num = int(end_part)
            for a in range(start_num, end_num + 1):
                normalized.add(f"{surah_num}:{a}")
        else:
            parts = item.split(":")
            normalized.add(f"{int(parts[0])}:{int(parts[1])}")
    return normalized

def calculate_citation_accuracy(predicted_text: str, expected_list: List[str]) -> float:
    """
    Scores the predicted citation overlap recall.
    score = |predicted ∩ expected| / |expected|
    """
    predicted = parse_verses_from_text(predicted_text)
    expected = parse_expected_verses(expected_list)
    
    if not expected:
        return 1.0 if not predicted else 0.0
        
    overlap = predicted.intersection(expected)
    return len(overlap) / len(expected)

def is_valid_verse_reference(ref: str) -> bool:
    """
    Checks if a parsed reference (e.g., "2:275") represents a valid verse in the Quran.
    """
    try:
        parts = ref.split(":")
        surah = int(parts[0])
        ayah = int(parts[1])
        
        if surah < 1 or surah > 114:
            return False
            
        max_ayahs = SURAH_VERSE_COUNTS.get(surah, 0)
        return 1 <= ayah <= max_ayahs
    except Exception:
        return False

def check_for_hallucinated_citations(predicted_text: str) -> List[str]:
    """
    Scans predicted text and returns a list of references that do not exist in the Quran.
    """
    predicted = parse_verses_from_text(predicted_text)
    hallucinated = []
    for ref in predicted:
        if not is_valid_verse_reference(ref):
            hallucinated.append(ref)
    return hallucinated

if __name__ == "__main__":
    print("=== Citation Accuracy Metric Tester ===")
    
    # Test case 1
    test_text = "As stated in Al-Baqarah (2:275-278) and Ali 'Imran 3:130."
    expected = ["2:275", "2:276", "2:277", "2:278", "2:279"]
    
    score = calculate_citation_accuracy(test_text, expected)
    print(f"Parsed predicted: {parse_verses_from_text(test_text)}")
    print(f"Normalized expected: {parse_expected_verses(expected)}")
    print(f"Recall Score: {score:.4f}")
    
    # Test case 2: Hallucination check
    hallucinations_text = "See Surah 2:300 and Surah 115:1."
    print(f"Scanning for hallucinations: '{hallucinations_text}'")
    halls = check_for_hallucinated_citations(hallucinations_text)
    print(f"  Hallucinated refs found: {halls}")
