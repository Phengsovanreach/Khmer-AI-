"""
Khmer Natural Language Processing, Unicode Normalization, and Context-Aware Proofreading Engine.

Provides:
1. Canonical Khmer Unicode Normalization & Diacritic Sequence Repair.
2. Number, Digit, Date, and Abbreviation Expansion into spoken Khmer phonetics.
3. Custom Pronunciation and Terminology Dictionary Management with disk persistence.
4. Context-Aware Khmer Grammar, Spelling, and Punctuation Proofreading with structured diffs.
5. Text normalization specifically tuned for Microsoft Neural Khmer TTS (Piseth & Sreymom).
"""

from __future__ import annotations
import difflib
import json
import logging
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import BASE_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

# Dictionary storage location
DICTIONARY_FILE = (BASE_DIR / "pronunciation_dictionary.json").resolve()
_DICT_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# 1. KHMER UNICODE CONSTANTS & CANONICAL ORDERING
# ---------------------------------------------------------------------------
# Consonants: U+1780 to U+17B3
KHMER_CONSONANTS = set(chr(cp) for cp in range(0x1780, 0x17B4))
# Independent Vowels: U+17A3 to U+17B3 (subset)
KHMER_INDEP_VOWELS = set(chr(cp) for cp in range(0x17A3, 0x17B4))
# Coeng (Subscript Sign): U+17D2
COENG = "\u17D2"
# Dependent Vowels: U+17B6 to U+17C5
KHMER_DEP_VOWELS = set(chr(cp) for cp in range(0x17B6, 0x17C6))
# Signs and Diacritics: U+17C6 to U+17D3
KHMER_DIACRITICS = set(chr(cp) for cp in range(0x17C6, 0x17D4) if cp != 0x17D2)

# Specific diacritics
NIKAHIT = "\u17C6"       # ំ
REAHMUK = "\u17C7"       # ះ
YUUKALEAPINTU = "\u17C8" # ៈ
MUUSIKOATOAN = "\u17C9"  # ៉
TRIISAP = "\u17CA"       # ៊
BANTOK = "\u17CB"        # ់
ROBAT = "\u17CC"         # ៌
TOANDAKHIAT = "\u17CD"   # ៍
KAKABAT = "\u17CE"       # ៎
AHASDAI = "\u17CF"       # ៏
SAMYOK_SANNYA = "\u17D0" # ័
VIRIAM = "\u17D1"        # ៑

KH_ZERO_WIDTH_SPACE = "\u200B"
KH_KHAN = "\u17D4"       # ។
KH_BARIYOOSAN = "\u17D5" # ៕
KH_LEK_TO = "\u17D7"     # ៗ (Repetition sign)
KH_L_LA = "\u17D8"       # ៘ (Etc sign)

# Digits mapping
KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"
ARABIC_DIGITS = "0123456789"


# ---------------------------------------------------------------------------
# 2. KHMER NUMBER TO WORDS EXPANDER (Natural Spoken Khmer)
# ---------------------------------------------------------------------------
DIGIT_WORDS = {
    0: "សូន្យ",
    1: "មួយ",
    2: "ពីរ",
    3: "បី",
    4: "បួន",
    5: "ប្រាំ",
    6: "ប្រាំមួយ",
    7: "ប្រាំពីរ",
    8: "ប្រាំបី",
    9: "ប្រាំបួន",
}

TENS_WORDS = {
    10: "ដប់",
    20: "ម្ភៃ",
    30: "សាមសិប",
    40: "សែសិប",
    50: "ហាសិប",
    60: "ហុកសិប",
    70: "ចិតសិប",
    80: "ប៉ែតសិប",
    90: "កៅសិប",
}


def _integer_to_khmer_words(n: int) -> str:
    """Converts a positive integer into natural spoken Khmer words."""
    if n == 0:
        return "សូន្យ"
    if n < 0:
        return "ដក " + _integer_to_khmer_words(-n)

    if n < 10:
        return DIGIT_WORDS[n]
    if n < 100:
        tens = (n // 10) * 10
        rem = n % 10
        if rem == 0:
            return TENS_WORDS[tens]
        return f"{TENS_WORDS[tens]}{DIGIT_WORDS[rem]}"

    if n < 1000:
        hundreds = n // 100
        rem = n % 100
        h_str = f"{DIGIT_WORDS[hundreds]}រយ"
        if rem == 0:
            return h_str
        return f"{h_str}{_integer_to_khmer_words(rem)}"

    if n < 10000:
        thousands = n // 1000
        rem = n % 1000
        t_str = f"{DIGIT_WORDS[thousands]}ពាន់"
        if rem == 0:
            return t_str
        return f"{t_str}{_integer_to_khmer_words(rem)}"

    if n < 100000:
        ten_thousands = n // 10000
        rem = n % 10000
        tt_str = f"{DIGIT_WORDS[ten_thousands]}ម៉ឺន"
        if rem == 0:
            return tt_str
        return f"{tt_str}{_integer_to_khmer_words(rem)}"

    if n < 1000000:
        hundred_thousands = n // 100000
        rem = n % 100000
        ht_str = f"{DIGIT_WORDS[hundred_thousands]}សែន"
        if rem == 0:
            return ht_str
        return f"{ht_str}{_integer_to_khmer_words(rem)}"

    if n < 1000000000:
        millions = n // 1000000
        rem = n % 1000000
        m_str = f"{_integer_to_khmer_words(millions)}លាន"
        if rem == 0:
            return m_str
        return f"{m_str}{_integer_to_khmer_words(rem)}"

    # For extremely large numbers, pronounce digit group
    return " ".join(DIGIT_WORDS.get(int(d), d) for d in str(n))


def expand_khmer_numbers(text: str) -> str:
    """
    Finds numeric sequences (both Khmer and Arabic digits) and expands them
    into natural spoken Khmer words.
    E.g. "ឆ្នាំ 2026" -> "ឆ្នាំ ពីរពាន់ម្ភៃប្រាំមួយ"
    E.g. "50%" -> "ហាសិបភាគរយ"
    E.g. "$100" -> "មួយរយដុល្លារ"
    """
    if not text:
        return ""

    # Convert Khmer digits to Arabic digits for regex parsing
    def _kh_to_ar(s: str) -> str:
        res = []
        for ch in s:
            if ch in KHMER_DIGITS:
                res.append(str(KHMER_DIGITS.index(ch)))
            else:
                res.append(ch)
        return "".join(res)

    # Replace currency and percentage patterns first
    t = text
    # Currency $
    t = re.sub(
        r"\$\s*([0-9០-៩]+)",
        lambda m: f"{_integer_to_khmer_words(int(_kh_to_ar(m.group(1))))}ដុល្លារ",
        t,
    )
    # Currency Riel ៛
    t = re.sub(
        r"([0-9០-៩]+)\s*៛",
        lambda m: f"{_integer_to_khmer_words(int(_kh_to_ar(m.group(1))))}រៀល",
        t,
    )
    # Percentage %
    t = re.sub(
        r"([0-9០-៩]+)\s*%",
        lambda m: f"{_integer_to_khmer_words(int(_kh_to_ar(m.group(1))))}ភាគរយ",
        t,
    )

    # General number sequences (up to 9 digits)
    def _repl_num(match: re.Match) -> str:
        raw_digits = match.group(0)
        ar_digits = _kh_to_ar(raw_digits)
        try:
            val = int(ar_digits)
            return _integer_to_khmer_words(val)
        except ValueError:
            return raw_digits

    t = re.sub(r"[0-9០-៩]{1,9}", _repl_num, t)
    return t


# ---------------------------------------------------------------------------
# 3. KHMER UNICODE NORMALIZATION & DIACRITIC REPAIR
# ---------------------------------------------------------------------------
def normalize_khmer_unicode(text: str) -> str:
    """
    Normalizes Khmer text into canonical Unicode ordering:
    - Removes duplicate consecutive vowels (e.g. ាា -> ា).
    - Fixes duplicate Bantoc or diacritics (e.g. ់់ -> ់).
    - Repositions Bantoc (U+17CB) after dependent vowels if inverted.
    - Normalizes Reahmuk (U+17C7) and Nikahit (U+17C6).
    - Strips useless multiple zero-width spaces or cleans spacing around Khmer punctuation.
    - Standardizes western periods '.' to Khmer Khan '។' at sentence ends.
    """
    if not text:
        return ""

    s = text

    # 1. Normalize duplicate dependent vowels
    for v in KHMER_DEP_VOWELS:
        s = s.replace(v + v, v)

    # 2. Normalize duplicate diacritics
    for d in (BANTOK, NIKAHIT, REAHMUK, SAMYOK_SANNYA, MUUSIKOATOAN, TRIISAP):
        s = s.replace(d + d, d)

    # 3. Fix misplaced Bantok (Bantoc must come after vowel if vowel is present)
    # E.g. \u17cb\u17b6 -> \u17b6\u17cb
    s = re.sub(f"({BANTOK})([{KHMER_DEP_VOWELS}])", r"\2\1", s)

    # 4. Standardize Coeng sequence (COENG + COENG -> COENG)
    s = s.replace(COENG + COENG, COENG)

    # 5. Fix multiple consecutive Zero-Width Spaces
    s = re.sub(f"{KH_ZERO_WIDTH_SPACE}+", KH_ZERO_WIDTH_SPACE, s)

    # 6. Spacing around Khmer Khan punctuation
    # Khmer Khan '។' should not be preceded by multiple spaces, but followed by a space
    s = re.sub(r"\s*។\s*", "។ ", s)
    s = re.sub(r"\s*៕\s*", "៕ ", s)

    # 7. Convert western sentence terminator '.' to '។' when surrounded by Khmer text
    # e.g., "សួស្តី." -> "សួស្តី។ "
    s = re.sub(r"([\u1780-\u17D3])\s*\.\s*(?=$|\n|[\u1780-\u17D3A-Z])", r"\1។ ", s)

    return s.strip()


# ---------------------------------------------------------------------------
# 4. PRONUNCIATION & TERMINOLOGY DICTIONARY
# ---------------------------------------------------------------------------
DEFAULT_DICTIONARY_ENTRIES: list[dict[str, Any]] = [
    # AI & Modern Technology
    {"term": "AI", "replacement": "បញ្ញាសិប្បនិម្មិត", "category": "tech", "notes": "Artificial Intelligence"},
    {"term": "A.I.", "replacement": "បញ្ញាសិប្បនិម្មិត", "category": "tech", "notes": "Abbreviation"},
    {"term": "Video", "replacement": "វីដេអូ", "category": "media", "notes": "Standard Khmer spelling"},
    {"term": "Videos", "replacement": "វីដេអូ", "category": "media", "notes": "Plural form"},
    {"term": "Audio", "replacement": "សំឡេង", "category": "media", "notes": "Audio / Voice"},
    {"term": "Subtitle", "replacement": "ចំណងជើងរង", "category": "media", "notes": "Subtitle / Hardsub"},
    {"term": "Subtitles", "replacement": "ចំណងជើងរង", "category": "media", "notes": "Subtitles plural"},
    {"term": "Dubbing", "replacement": "បញ្ចូលសំឡេង", "category": "media", "notes": "Voice dubbing"},
    {"term": "Dubbed", "replacement": "បញ្ចូលសំឡេងរួច", "category": "media", "notes": "Dubbed past participle"},
    {"term": "YouTube", "replacement": "យូធូប", "category": "brand", "notes": "Platform name"},
    {"term": "Google", "replacement": "ហ្គូហ្គល", "category": "brand", "notes": "Tech brand"},
    {"term": "Facebook", "replacement": "ហ្វេសប៊ុក", "category": "brand", "notes": "Social platform"},
    {"term": "TikTok", "replacement": "ទីកតុក", "category": "brand", "notes": "Social platform"},
    {"term": "CEO", "replacement": "អគ្គនាយក", "category": "business", "notes": "Chief Executive Officer"},
    {"term": "Khmer", "replacement": "ខ្មែរ", "category": "culture", "notes": "Language / Nation"},
    {"term": "Cambodia", "replacement": "កម្ពុជា", "category": "geography", "notes": "Country"},
    {"term": "Angkor", "replacement": "អង្គរ", "category": "culture", "notes": "Heritage site"},
    {"term": "Phnom Penh", "replacement": "ភ្នំពេញ", "category": "geography", "notes": "Capital city"},
    # Common Spelling Corrections
    {"term": "វីឌីអូ", "replacement": "វីដេអូ", "category": "spelling", "notes": "Correct spelling of video"},
    {"term": "អរគុណច្រើន", "replacement": "សូមអរគុណច្រើន", "category": "courtesy", "notes": "Polite form"},
    {"term": "បកប្រែពាក្យ", "replacement": "បកប្រែ", "category": "grammar", "notes": "Concise natural phrasing"},
]


class DictionaryManager:
    """Manages the editable terminology and pronunciation dictionary."""

    def __init__(self, filepath: Path = DICTIONARY_FILE) -> None:
        self.filepath = filepath
        self._entries: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        with _DICT_LOCK:
            if self.filepath.exists():
                try:
                    data = json.loads(self.filepath.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        self._entries = data
                        return
                except Exception as exc:
                    logger.warning("Failed to load dictionary from %s: %s", self.filepath, exc)

            # Initialize with default entries
            self._entries = list(DEFAULT_DICTIONARY_ENTRIES)
            self._save_unlocked()

    def _save_unlocked(self) -> None:
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.filepath.write_text(
                json.dumps(self._entries, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Failed to save dictionary to %s: %s", self.filepath, exc)

    def get_all(self) -> list[dict[str, Any]]:
        with _DICT_LOCK:
            return list(self._entries)

    def add_or_update(
        self,
        term: str,
        replacement: str,
        category: str = "general",
        notes: str = "",
        case_sensitive: bool = False,
    ) -> dict[str, Any]:
        term_clean = term.strip()
        rep_clean = replacement.strip()
        if not term_clean or not rep_clean:
            raise ValueError("Term and replacement cannot be empty")

        with _DICT_LOCK:
            found = False
            entry_out: dict[str, Any] = {}
            for item in self._entries:
                if item["term"].lower() == term_clean.lower():
                    item["replacement"] = rep_clean
                    item["category"] = category
                    item["notes"] = notes
                    item["case_sensitive"] = case_sensitive
                    item["updated_at"] = datetime.now().isoformat()
                    found = True
                    entry_out = item
                    break

            if not found:
                entry_out = {
                    "term": term_clean,
                    "replacement": rep_clean,
                    "category": category,
                    "notes": notes,
                    "case_sensitive": case_sensitive,
                    "created_at": datetime.now().isoformat(),
                }
                self._entries.append(entry_out)

            self._save_unlocked()
            return entry_out

    def delete(self, term: str) -> bool:
        term_lower = term.strip().lower()
        with _DICT_LOCK:
            orig_len = len(self._entries)
            self._entries = [e for e in self._entries if e["term"].lower() != term_lower]
            if len(self._entries) != orig_len:
                self._save_unlocked()
                return True
            return False

    def apply_to_text(self, text: str) -> tuple[str, list[dict[str, Any]]]:
        """
        Applies terminology replacements to text.
        Returns (transformed_text, list_of_applied_replacements).
        """
        if not text:
            return "", []

        result = text
        applied: list[dict[str, Any]] = []

        with _DICT_LOCK:
            # Sort by length descending so longer phrases match first
            sorted_entries = sorted(self._entries, key=lambda x: len(x["term"]), reverse=True)
            for entry in sorted_entries:
                term = entry["term"]
                rep = entry["replacement"]
                case_sensitive = entry.get("case_sensitive", False)

                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.escape(term)
                # If latin word, add word boundary check
                if term.isascii() and term.isalpha():
                    pattern = rf"\b{pattern}\b"

                matches = list(re.finditer(pattern, result, flags=flags))
                if matches:
                    result = re.sub(pattern, rep, result, flags=flags)
                    applied.append({
                        "term": term,
                        "replacement": rep,
                        "category": entry.get("category", "general"),
                        "count": len(matches),
                    })

        return result, applied


dictionary_manager = DictionaryManager()


# ---------------------------------------------------------------------------
# 5. CONTEXT-AWARE KHMER PROOFREADER
# ---------------------------------------------------------------------------
# Common literal translation patterns that sound unnatural in Khmer
KHMER_GRAMMAR_PATTERNS: list[tuple[re.Pattern, str, str, str]] = [
    # (regex_pattern, replacement, reason, issue_type)
    (
        re.compile(r"ខ្ញុំគិតថាវាគឺជា", re.IGNORECASE),
        "ខ្ញុំគិតថាវាជា",
        "លុបពាក្យ 'គឺ' ចេញ ដើម្បីឱ្យឃ្លាស្តាប់ទៅកាន់តែធម្មជាតិ",
        "grammar",
    ),
    (
        re.compile(r"តើអ្នកសុខសប្បាយជាទេ\?", re.IGNORECASE),
        "តើអ្នកសុខសប្បាយទេ?",
        "កែសម្រួលឃ្លាសួរសុខទុក្ខឱ្យត្រូវតាមទម្លាប់និយាយខ្មែរ",
        "grammar",
    ),
    (
        re.compile(r"មួយចំនួនធំនៃ", re.IGNORECASE),
        "ភាគច្រើននៃ",
        "កែប្រែឃ្លាបកប្រែតាមន័យចំ (literal) ទៅជាឃ្លាខ្មែរធម្មជាតិ",
        "grammar",
    ),
    (
        re.compile(r"នៅក្នុងពេលឥឡូវនេះ", re.IGNORECASE),
        "នៅពេលនេះ",
        "សម្រួលឃ្លាឱ្យខ្លី និងច្បាស់លាស់",
        "grammar",
    ),
    (
        re.compile(r"មានអារម្មណ៍ល្អអំពី", re.IGNORECASE),
        "ពេញចិត្តនឹង",
        "កែសម្រួលឃ្លា 'feel good about' មកជាឃ្លាខ្មែរសមរម្យ",
        "grammar",
    ),
    (
        re.compile(r"(\b|\s)(គាត់|នាង)បានធ្វើការ(ដើរ|រត់|និយាយ)", re.IGNORECASE),
        r"\1\2បាន\3",
        "លុបពាក្យ 'ធ្វើការ' ចេញពីកិរិយាស័ព្ទធម្មតា",
        "grammar",
    ),
    (
        re.compile(r"អរគុណចំពោះការទស្សនា", re.IGNORECASE),
        "សូមអរគុណសម្រាប់ការទស្សនា",
        "ទម្រង់គួរសមផ្លូវការសម្រាប់បញ្ចប់វីដេអូ",
        "courtesy",
    ),
]


def _compute_diffs(old_str: str, new_str: str) -> list[dict[str, Any]]:
    """Calculates clean token-level or character-level diffs between old and new text."""
    diffs: list[dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, old_str, new_str)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diffs.append({"op": "equal", "text": old_str[i1:i2]})
        elif tag == "delete":
            diffs.append({"op": "delete", "text": old_str[i1:i2], "old_text": old_str[i1:i2]})
        elif tag == "insert":
            diffs.append({"op": "insert", "text": new_str[j1:j2], "new_text": new_str[j1:j2]})
        elif tag == "replace":
            diffs.append({
                "op": "replace",
                "text": new_str[j1:j2],
                "old_text": old_str[i1:i2],
                "new_text": new_str[j1:j2],
            })
    return diffs


class KhmerProofreader:
    """
    Context-aware proofreader for Khmer translated subtitle segments.
    Detects spelling, vowels/diacritics, unnatural grammar, numbers, and terminology.
    """

    def proofread_text(
        self,
        text: str,
        source_text: str = "",
        context_story: str = "",
        style: str = "conversational",
    ) -> dict[str, Any]:
        """
        Proofreads a single dialogue line.
        Returns:
            {
                "original_source": str,
                "initial_translation": str,
                "suggested_khmer": str,
                "issues": list[dict],
                "diffs": list[dict],
                "confidence": float,
            }
        """
        raw_translation = text.strip()
        if not raw_translation:
            return {
                "original_source": source_text,
                "initial_translation": "",
                "suggested_khmer": "",
                "issues": [],
                "diffs": [],
                "confidence": 1.0,
            }

        issues: list[dict[str, Any]] = []

        # Step 1: Khmer Unicode Normalization & Diacritic Sequence Repair
        normalized_unicode = normalize_khmer_unicode(raw_translation)
        if normalized_unicode != raw_translation:
            issues.append({
                "type": "diacritic",
                "original": raw_translation,
                "replacement": normalized_unicode,
                "reason": "កែសម្រួលលំដាប់ស្រៈ និងសញ្ញាឱ្យស្របតាមក្បួនខ្នាតយូនីកូដខ្មែរ",
                "confidence": 0.98,
            })

        # Step 2: Terminology and Custom Pronunciation Dictionary
        after_dict, applied_terms = dictionary_manager.apply_to_text(normalized_unicode)
        for term_info in applied_terms:
            issues.append({
                "type": "terminology",
                "original": term_info["term"],
                "replacement": term_info["replacement"],
                "reason": f"អនុវត្តតាមវចនានុក្រមបច្ចេកសព្ទ ({term_info['category']})",
                "confidence": 0.99,
            })

        # Step 3: Khmer Number Expansion (Digits -> Spoken Words)
        after_numbers = expand_khmer_numbers(after_dict)
        if after_numbers != after_dict:
            issues.append({
                "type": "number_format",
                "original": after_dict,
                "replacement": after_numbers,
                "reason": "ពង្រីកលេខឱ្យទៅជាពាក្យអានពេញលេញសម្រាប់សូរសំឡេងធម្មជាតិ",
                "confidence": 0.96,
            })

        # Step 4: Context & Natural Grammar Patterns
        current = after_numbers
        for pat, rep, reason, itype in KHMER_GRAMMAR_PATTERNS:
            if pat.search(current):
                new_val = pat.sub(rep, current)
                if new_val != current:
                    issues.append({
                        "type": itype,
                        "original": current,
                        "replacement": new_val,
                        "reason": reason,
                        "confidence": 0.90,
                    })
                    current = new_val

        # Step 5: Repetitive duplicated words check (e.g. "និង និង" -> "និង")
        dup_pattern = re.compile(r"([\u1780-\u17D3]+)\s+\1(\s|$|។)")
        if dup_pattern.search(current):
            cleaned_dup = dup_pattern.sub(r"\1\2", current)
            if cleaned_dup != current:
                issues.append({
                    "type": "spelling",
                    "original": current,
                    "replacement": cleaned_dup,
                    "reason": "លុបពាក្យដែលបានសរសេរត្រួតជាន់គ្នាដោយចៃដន្យ",
                    "confidence": 0.94,
                })
                current = cleaned_dup

        # Step 6: Style and Pronoun Consistency
        if style == "formal":
            # Replace informal pronouns with formal pronouns
            formalized = re.sub(r"\bឯង\b", "អ្នក", current)
            formalized = re.sub(r"\bអញ\b", "ខ្ញុំ", formalized)
            if formalized != current:
                issues.append({
                    "type": "grammar",
                    "original": current,
                    "replacement": formalized,
                    "reason": "កែប្រែសព្វនាមឱ្យត្រូវតាមកម្រិតភាសាផ្លូវការ (Formal Context)",
                    "confidence": 0.88,
                })
                current = formalized

        suggested_khmer = normalize_khmer_unicode(current)
        diffs = _compute_diffs(raw_translation, suggested_khmer)

        # Realistic confidence based on issues detected
        if not issues:
            confidence = 1.0
        else:
            confidence = round(sum(i["confidence"] for i in issues) / len(issues), 2)

        return {
            "original_source": source_text,
            "initial_translation": raw_translation,
            "suggested_khmer": suggested_khmer,
            "issues": issues,
            "diffs": diffs,
            "confidence": confidence,
        }

    def proofread_segments(
        self,
        segments: list[dict[str, Any]],
        source_segments: list[dict[str, Any]] | None = None,
        context_story: str = "",
        style: str = "conversational",
        auto_apply_high_confidence: bool = False,
    ) -> dict[str, Any]:
        """
        Proofreads all segments of a video subtitle track in context.
        """
        src_map: dict[int, str] = {}
        if source_segments:
            for s in source_segments:
                src_map[s.get("id", 0)] = str(s.get("text", ""))

        results: list[dict[str, Any]] = []
        summary = {
            "total_segments": len(segments),
            "segments_with_issues": 0,
            "total_issues": 0,
            "auto_applied_count": 0,
            "spelling_issues": 0,
            "grammar_issues": 0,
            "terminology_issues": 0,
            "number_issues": 0,
            "diacritic_issues": 0,
        }

        for seg in segments:
            seg_id = seg.get("id", len(results) + 1)
            trans_text = str(seg.get("text", ""))
            src_text = src_map.get(seg_id, "")

            res = self.proofread_text(
                text=trans_text,
                source_text=src_text,
                context_story=context_story,
                style=style,
            )

            res["segment_id"] = seg_id
            res["start"] = seg.get("start", 0.0)
            res["end"] = seg.get("end", 0.0)
            res["speaker_id"] = seg.get("speaker_id")

            # Check if auto applied
            if auto_apply_high_confidence and res["confidence"] >= 0.85 and res["issues"]:
                res["applied_automatically"] = True
                summary["auto_applied_count"] += 1
            else:
                res["applied_automatically"] = False

            if res["issues"]:
                summary["segments_with_issues"] += 1
                summary["total_issues"] += len(res["issues"])
                for issue in res["issues"]:
                    itype = issue.get("type", "grammar")
                    if itype == "spelling":
                        summary["spelling_issues"] += 1
                    elif itype == "grammar":
                        summary["grammar_issues"] += 1
                    elif itype == "terminology":
                        summary["terminology_issues"] += 1
                    elif itype == "number_format":
                        summary["number_issues"] += 1
                    elif itype == "diacritic":
                        summary["diacritic_issues"] += 1

            results.append(res)

        return {
            "results": results,
            "summary": summary,
            "total_issues": summary["total_issues"],
        }


khmer_proofreader = KhmerProofreader()


# ---------------------------------------------------------------------------
# 6. TEXT PREPARATION TUNED SPECIFICALLY FOR KHMER TTS
# ---------------------------------------------------------------------------
def normalize_khmer_for_tts(text: str) -> str:
    """
    Cleans, normalizes, and prepares Khmer text specifically before feeding
    into Edge-TTS (Piseth / Sreymom).
    - Normalizes Unicode and removes duplicate diacritics.
    - Expands numeric sequences into spoken Khmer words.
    - Applies custom pronunciation and terminology mappings.
    - Adjusts pause markers: converts '។' to clean pauses for natural breathing.
    """
    if not text or not text.strip():
        return ""

    # 1. Unicode normalization
    cleaned = normalize_khmer_unicode(text.strip())

    # 2. Terminology dictionary substitution
    cleaned, _ = dictionary_manager.apply_to_text(cleaned)

    # 3. Number expansion
    cleaned = expand_khmer_numbers(cleaned)

    # 4. Remove unwanted symbols that cause TTS hesitation
    cleaned = re.sub(r"[\"\"''«»`~^]", "", cleaned)

    # 5. Clean punctuation pauses
    # Ensure a single space after Khmer Khan '។' for natural sentence boundary pause
    cleaned = re.sub(r"។+", "។ ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned
