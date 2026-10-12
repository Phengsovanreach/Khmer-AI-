"""
Test Suite for Khmer Language Accuracy, Unicode Normalization,
Spoken Number Expansion, Terminology Dictionary, and Proofreading Engine.
"""

import pytest
from fastapi.testclient import TestClient

from app.khmer_nlp import (
    dictionary_manager,
    expand_khmer_numbers,
    khmer_proofreader,
    normalize_khmer_for_tts,
    normalize_khmer_unicode,
)
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Unicode Normalization & Diacritic Sequence Tests
# ---------------------------------------------------------------------------
def test_khmer_unicode_vowel_deduplication():
    # Duplicate 'AA' vowel (U+17B6)
    bad_vowel = "កាា"
    fixed = normalize_khmer_unicode(bad_vowel)
    assert fixed == "កា"


def test_khmer_unicode_diacritic_deduplication():
    # Duplicate Bantok (U+17CB)
    bad_bantok = "កាត់់"
    fixed = normalize_khmer_unicode(bad_bantok)
    assert fixed == "កាត់"


def test_khmer_unicode_punctuation_khan():
    # Western period at sentence end converted to Khmer Khan '។'
    text = "សួស្តីអ្នកទាំងអស់គ្នា."
    fixed = normalize_khmer_unicode(text)
    assert "។" in fixed


# ---------------------------------------------------------------------------
# 2. Spoken Khmer Number Expansion Tests
# ---------------------------------------------------------------------------
def test_khmer_number_expansion_digits():
    # Single digit
    assert expand_khmer_numbers("1") == "មួយ"
    assert expand_khmer_numbers("១") == "មួយ"

    # Tens and composite numbers
    assert expand_khmer_numbers("10") == "ដប់"
    assert expand_khmer_numbers("25") == "ម្ភៃប្រាំ"
    assert expand_khmer_numbers("១០០") == "មួយរយ"

    # Year 2026
    year_ar = expand_khmer_numbers("2026")
    year_kh = expand_khmer_numbers("២០២៦")
    assert year_ar == "ពីរពាន់ម្ភៃប្រាំមួយ"
    assert year_kh == "ពីរពាន់ម្ភៃប្រាំមួយ"


def test_khmer_percentage_and_currency():
    pct = expand_khmer_numbers("50%")
    assert "ហាសិបភាគរយ" in pct

    curr = expand_khmer_numbers("$10")
    assert "ដប់ដុល្លារ" in curr


# ---------------------------------------------------------------------------
# 3. Terminology & Pronunciation Dictionary Tests
# ---------------------------------------------------------------------------
def test_dictionary_manager_apply():
    text = "I love this AI Video"
    result, applied = dictionary_manager.apply_to_text(text)
    assert "បញ្ញាសិប្បនិម្មិត" in result
    assert "វីដេអូ" in result
    assert len(applied) >= 2


def test_dictionary_crud():
    # Add custom term
    entry = dictionary_manager.add_or_update(
        term="SuperTestBot",
        replacement="រ៉ូបូតសាកល្បងទំនើប",
        category="testing",
        notes="Automated test entry",
    )
    assert entry["term"] == "SuperTestBot"

    # Apply
    out, applied = dictionary_manager.apply_to_text("Welcome SuperTestBot here")
    assert "រ៉ូបូតសាកល្បងទំនើប" in out

    # Delete
    deleted = dictionary_manager.delete("SuperTestBot")
    assert deleted is True


# ---------------------------------------------------------------------------
# 4. Context-Aware Proofreading Tests
# ---------------------------------------------------------------------------
def test_proofread_text_grammar_improvement():
    # Literal phrasing: "ខ្ញុំគិតថាវាគឺជា" -> "ខ្ញុំគិតថាវាជា"
    raw = "ខ្ញុំគិតថាវាគឺជាការងារល្អ។"
    res = khmer_proofreader.proofread_text(raw, source_text="I think it is good work.")
    assert "issues" in res
    assert "suggested_khmer" in res
    assert "diffs" in res
    assert "ខ្ញុំគិតថាវាជា" in res["suggested_khmer"]


def test_proofread_segments_batch():
    segments = [
        {"id": 1, "start": 0.0, "end": 2.5, "text": "សួស្តី វីឌីអូ នេះគឺ 100% ល្អ។"},
        {"id": 2, "start": 2.5, "end": 5.0, "text": "ខ្ញុំគិតថាវាគឺជាការចាប់ផ្ដើម។"},
    ]
    batch_res = khmer_proofreader.proofread_segments(
        segments=segments,
        style="conversational",
        auto_apply_high_confidence=True,
    )
    assert "results" in batch_res
    assert len(batch_res["results"]) == 2
    assert batch_res["summary"]["total_issues"] > 0
    # Check that 'វីឌីអូ' was corrected to 'វីដេអូ'
    assert "វីដេអូ" in batch_res["results"][0]["suggested_khmer"]


def test_normalize_khmer_for_tts():
    raw = "ឆ្នាំ 2026 មាន AI Video 100%"
    tts_ready = normalize_khmer_for_tts(raw)
    assert "ពីរពាន់ម្ភៃប្រាំមួយ" in tts_ready
    assert "បញ្ញាសិប្បនិម្មិត" in tts_ready
    assert "វីដេអូ" in tts_ready


# ---------------------------------------------------------------------------
# 5. API Endpoints Integration Tests
# ---------------------------------------------------------------------------
def test_api_dictionary_endpoints(client):
    # GET list
    resp = client.get("/api/dictionary")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert data["total"] > 0

    # POST add
    add_resp = client.post(
        "/api/dictionary",
        json={
            "term": "TestPhrase123",
            "replacement": "ឃ្លាសាកល្បង១២៣",
            "category": "test",
            "notes": "API test",
        },
    )
    assert add_resp.status_code == 200
    assert add_resp.json()["term"] == "TestPhrase123"

    # DELETE
    del_resp = client.delete("/api/dictionary/TestPhrase123")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"


def test_api_proofread_sample_endpoint(client):
    resp = client.post(
        "/api/proofread-sample",
        json={
            "text": "វីឌីអូ នេះល្អណាស់",
            "source_text": "This video is very good",
            "style": "conversational",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "suggested_khmer" in data
    assert "issues" in data
    assert "diffs" in data
    assert "វីដេអូ" in data["suggested_khmer"]
