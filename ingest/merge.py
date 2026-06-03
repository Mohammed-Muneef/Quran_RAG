#!/usr/bin/env python3
import json
from pathlib import Path

# Surah details helper dictionary mapping number -> (English Name, Arabic Name, Revelation Type)
SURAH_METADATA = {
    1: ("Al-Fatihah", "الفاتحة", "Meccan"),
    2: ("Al-Baqarah", "البقرة", "Medinan"),
    3: ("Ali 'Imran", "آل عمران", "Medinan"),
    4: ("An-Nisa", "النساء", "Medinan"),
    5: ("Al-Ma'idah", "المائدة", "Medinan"),
    6: ("Al-An'am", "الأنعام", "Meccan"),
    7: ("Al-A'raf", "الأعراف", "Meccan"),
    8: ("Al-Anfal", "الأنفال", "Medinan"),
    9: ("At-Tawbah", "التوبة", "Medinan"),
    10: ("Yunus", "يونس", "Meccan"),
    11: ("Hud", "هود", "Meccan"),
    12: ("Yusuf", "يوسف", "Meccan"),
    13: ("Ar-Ra'd", "الرعد", "Medinan"),
    14: ("Ibrahim", "ابراهيم", "Meccan"),
    15: ("Al-Hijr", "الحجر", "Meccan"),
    16: ("An-Nahl", "النحل", "Meccan"),
    17: ("Al-Isra", "الإسراء", "Meccan"),
    18: ("Al-Kahf", "الكهف", "Meccan"),
    19: ("Maryam", "مريم", "Meccan"),
    20: ("Ta-Ha", "طه", "Meccan"),
    21: ("Al-Anbiya", "الأنبياء", "Meccan"),
    22: ("Al-Hajj", "الحج", "Medinan"),
    23: ("Al-Mu'minun", "المؤمنون", "Meccan"),
    24: ("An-Nur", "النور", "Medinan"),
    25: ("Al-Furqan", "الفرقان", "Meccan"),
    26: ("Ash-Shu'ara", "الشعراء", "Meccan"),
    27: ("An-Naml", "النمل", "Meccan"),
    28: ("Al-Qasas", "القصص", "Meccan"),
    29: ("Al-'Ankabut", "العنكبوت", "Meccan"),
    30: ("Ar-Rum", "الروم", "Meccan"),
    31: ("Luqman", "لقمان", "Meccan"),
    32: ("As-Sajdah", "السجدة", "Meccan"),
    33: ("Al-Ahzab", "الأحزاب", "Medinan"),
    34: ("Saba", "سبأ", "Meccan"),
    35: ("Fatir", "فاطر", "Meccan"),
    36: ("Ya-Sin", "يس", "Meccan"),
    37: ("As-Saffat", "الصافات", "Meccan"),
    38: ("Sad", "ص", "Meccan"),
    39: ("Az-Zumar", "الزمر", "Meccan"),
    40: ("Ghafir", "غافر", "Meccan"),
    41: ("Fussilat", "فصلت", "Meccan"),
    42: ("Ash-Shura", "الشورى", "Meccan"),
    43: ("Az-Zukhruf", "الزخرف", "Meccan"),
    44: ("Ad-Dukhan", "الدخان", "Meccan"),
    45: ("Al-Jathiyah", "الجاثية", "Meccan"),
    46: ("Al-Ahqaf", "الأحقاف", "Meccan"),
    47: ("Muhammad", "محمد", "Medinan"),
    48: ("Al-Fath", "الفتح", "Medinan"),
    49: ("Al-Hujurat", "الحجرات", "Medinan"),
    50: ("Qaf", "ق", "Meccan"),
    51: ("Adh-Dhariyat", "الذاريات", "Meccan"),
    52: ("At-Tur", "الطور", "Meccan"),
    53: ("An-Najm", "النجم", "Meccan"),
    54: ("Al-Qamar", "القمر", "Meccan"),
    55: ("Ar-Rahman", "الرحمن", "Medinan"),
    56: ("Al-Waqi'ah", "الواقعة", "Meccan"),
    57: ("Al-Hadid", "الحديد", "Medinan"),
    58: ("Al-Mujadila", "المجادلة", "Medinan"),
    59: ("Al-Hashr", "الحشر", "Medinan"),
    60: ("Al-Mumtahanah", "الممتحنة", "Medinan"),
    61: ("As-Saf", "الصف", "Medinan"),
    62: ("Al-Jumu'ah", "الجمعة", "Medinan"),
    63: ("Al-Munafiqun", "المنافقون", "Medinan"),
    64: ("At-Taghabun", "التغابن", "Medinan"),
    65: ("At-Talaq", "الطلاق", "Medinan"),
    66: ("At-Tahrim", "التحريم", "Medinan"),
    67: ("Al-Mulk", "الملك", "Meccan"),
    68: ("Al-Qalam", "القلم", "Meccan"),
    69: ("Al-Haqqah", "الحاقة", "Meccan"),
    70: ("Al-Ma'arij", "المعارج", "Meccan"),
    71: ("Nuh", "نوح", "Meccan"),
    72: ("Al-Jinn", "الجن", "Meccan"),
    73: ("Al-Muzzammil", "المزمل", "Meccan"),
    74: ("Al-Muddaththir", "المدثر", "Meccan"),
    75: ("Al-Qiyamah", "القيامة", "Meccan"),
    76: ("Al-Insan", "الإنسان", "Medinan"),
    77: ("Al-Mursalat", "المرسلات", "Meccan"),
    78: ("An-Naba", "النبأ", "Meccan"),
    79: ("An-Nazi'at", "النازعات", "Meccan"),
    80: ("'Abasa", "عبس", "Meccan"),
    81: ("At-Takwir", "التكوير", "Meccan"),
    82: ("Al-Infitar", "الانفطار", "Meccan"),
    83: ("Al-Mutaffifin", "المطففين", "Meccan"),
    84: ("Al-Inshiqaq", "الانشقاق", "Meccan"),
    85: ("Al-Buruj", "البروج", "Meccan"),
    86: ("At-Tariq", "الطارق", "Meccan"),
    87: ("Al-A'la", "الأعلى", "Meccan"),
    88: ("Al-Ghashiyah", "الغاشية", "Meccan"),
    89: ("Al-Fajr", "الفجر", "Meccan"),
    90: ("Al-Balad", "البلد", "Meccan"),
    91: ("Ash-Shams", "الشمس", "Meccan"),
    92: ("Al-Layl", "الليل", "Meccan"),
    93: ("Ad-Duha", "الضحى", "Meccan"),
    94: ("Ash-Sharh", "الشرح", "Meccan"),
    95: ("At-Tin", "التين", "Meccan"),
    96: ("Al-'Alaq", "العلق", "Meccan"),
    97: ("Al-Qadr", "القدر", "Meccan"),
    98: ("Al-Bayyinah", "البينة", "Medinan"),
    99: ("Az-Zalzalah", "الزلزلة", "Medinan"),
    100: ("Al-'Adiyat", "العاديات", "Meccan"),
    101: ("Al-Qari'ah", "القارعة", "Meccan"),
    102: ("At-Takathur", "التكاثر", "Meccan"),
    103: ("Al-'Asr", "العصر", "Meccan"),
    104: ("Al-Humazah", "الهمزة", "Meccan"),
    105: ("Al-Fil", "الفيل", "Meccan"),
    106: ("Quraysh", "قريش", "Meccan"),
    107: ("Al-Ma'un", "الماعون", "Meccan"),
    108: ("Al-Kawthar", "الكوثر", "Meccan"),
    109: ("Al-Kafirun", "الكافرون", "Meccan"),
    110: ("An-Nasr", "النصر", "Medinan"),
    111: ("Al-Masad", "المسد", "Meccan"),
    112: ("Al-Ikhlas", "الإخلاص", "Meccan"),
    113: ("Al-Falaq", "الفلق", "Meccan"),
    114: ("An-Nas", "الناس", "Meccan"),
}

# Approximate mapping of Surahs to Juzs (based on Surah structures)
def calculate_juz(surah_number: int, ayah_number: int) -> int:
    # A simple lookup dictionary for start offsets of juz positions in the Quran
    # format: (surah, ayah) -> juz_number
    juz_boundaries = [
        ((1, 1), 1),
        ((2, 142), 2),
        ((2, 253), 3),
        ((3, 93), 4),
        ((4, 24), 5),
        ((4, 148), 6),
        ((5, 82), 7),
        ((6, 111), 8),
        ((7, 88), 9),
        ((8, 41), 10),
        ((9, 93), 11),
        ((11, 6), 12),
        ((12, 53), 13),
        ((14, 53), 14), # approximate boundary (15:1)
        ((15, 1), 14),
        ((17, 1), 15),
        ((18, 75), 16),
        ((20, 1), 17),
        ((21, 1), 17),
        ((23, 1), 18),
        ((25, 21), 19),
        ((27, 56), 20),
        ((29, 46), 21),
        ((33, 31), 22),
        ((36, 28), 23),
        ((39, 32), 24),
        ((41, 47), 25),
        ((46, 1), 26),
        ((51, 31), 27),
        ((58, 1), 28),
        ((67, 1), 29),
        ((78, 1), 30)
    ]
    
    # Linear scan to find correct juz mapping
    current_juz = 1
    for boundary, juz_num in juz_boundaries:
        b_surah, b_ayah = boundary
        if surah_number > b_surah or (surah_number == b_surah and ayah_number >= b_ayah):
            current_juz = juz_num
    return current_juz

def merge_corpus():
    raw_arabic_path = Path("data/raw/quran_arabic.json")
    raw_english_path = Path("data/raw/quran_english.json")
    processed_dir = Path("data/processed")
    merged_output_path = processed_dir / "quran_merged.json"

    if not raw_arabic_path.exists() or not raw_english_path.exists():
        print("Error: Raw files missing. Run download.py first.")
        return

    print("Loading raw corpus files...")
    with open(raw_arabic_path, "r", encoding="utf-8") as f:
        arabic_data = json.load(f)
    with open(raw_english_path, "r", encoding="utf-8") as f:
        english_data = json.load(f)

    merged_verses = []
    
    # Sort keys by Surah & Ayah numbers numerically
    sorted_keys = sorted(arabic_data.keys(), key=lambda k: tuple(int(x) for x in k.split(":")))
    
    print("Merging layers...")
    for key in sorted_keys:
        surah_str, ayah_str = key.split(":")
        surah_num = int(surah_str)
        ayah_num = int(ayah_str)
        
        ar_text = arabic_data[key]
        en_text = english_data.get(key, "")
        
        meta = SURAH_METADATA.get(surah_num, ("Unknown", "Unknown", "Meccan"))
        juz_num = calculate_juz(surah_num, ayah_num)
        
        merged_verse = {
            "surah_number": surah_num,
            "surah_name_en": meta[0],
            "surah_name_ar": meta[1],
            "ayah_number": ayah_num,
            "text_arabic": ar_text,
            "text_english": en_text,
            "revelation_type": meta[2],
            "juz": juz_num,
            "themes": [] # Will be populated during chunking or indexing if needed
        }
        merged_verses.append(merged_verse)

    processed_dir.mkdir(parents=True, exist_ok=True)
    with open(merged_output_path, "w", encoding="utf-8") as f:
        json.dump(merged_verses, f, ensure_ascii=False, indent=2)
    print(f"Saved merged corpus with {len(merged_verses):,} verses to {merged_output_path}")

    # Print a sample of 3 verses to verify
    print("\n--- Verification Sample ---")
    sample_indices = [0, 274, 6235] # First verse, index 275 (2:276 approx), and last verse
    for idx in sample_indices:
        if idx < len(merged_verses):
            v = merged_verses[idx]
            print(f"Reference: {v['surah_name_en']} ({v['surah_number']}:{v['ayah_number']}) | Juz: {v['juz']}")
            print(f"  Arabic: {v['text_arabic']}")
            print(f"  English: {v['text_english']}")
            print("-" * 50)

if __name__ == "__main__":
    merge_corpus()
