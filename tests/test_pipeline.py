"""
tests/test_pipeline.py
----------------------
Unit tests for all three pipeline stages.
Run with: pytest tests/ -v
No API keys required — tests validate logic only.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processor import load_transcript, _extract_metadata, _parse_segments, _clean_text, TranscriptData
from llm_processor  import RecapScript, _extract_section, _parse_key_points, _parse_quiz, _assemble_script
from tts_generator  import AudioResult, _chunk_text, _estimate_duration, _safe_filename


SAMPLE = """TRANSCRIPT — AI Consulting | Module 1, Class 3
Date: April 24, 2026
Instructor: Prof. Sarah Kim

[00:00] Good morning everyone. Today we cover APIs, data pipelines, and prompt engineering.

[05:00] An API is a contract between two systems. REST APIs use HTTP methods:
GET retrieves data, POST sends it, PUT updates, DELETE removes.

[10:00] Data pipelines follow ETL: Extract, Transform, Load.
Always handle errors. A silent failure is the worst kind.

[15:00] Prompt engineering: be specific. Vague prompts produce vague outputs.
Read chapters 4 and 5 before Thursday. See you then.
"""

MOCK_LLM = """
[INTRO]
Welcome back to your AI Consulting recap for April 24.
This is the class where everything started clicking together.

[STORY SETUP]
Imagine trying to connect two software systems with no shared language.
That is exactly the problem today solves.

[OVERVIEW]
Today covered REST APIs, ETL data pipelines, and prompt engineering basics.

[KEY POINTS]
REST APIs: A contract between two systems using HTTP. You need GET, POST, PUT, DELETE for every integration.
ETL Pipelines: Extract, Transform, Load. The three stages every data pipeline follows without exception.
Prompt Engineering: Be specific. Vague prompts produce vague outputs every single time.

[STORY CLIMAX]
With APIs, pipelines, and prompting skills combined, you can now build a complete data-driven system.
Each piece connects to the next — APIs feed data into pipelines, pipelines feed structured data to LLMs.

[DEEPER DIVE]
ETL is the backbone of every data system. Think of it like a factory assembly line.
Raw materials come in through Extract. Workers reshape them in Transform. Finished goods ship out through Load.
The most critical rule: always handle errors. A silent failure is always discovered at the worst moment.

[QUIZ]
What does a 401 HTTP status code mean and what should you do next?
What is the difference between Extract and Transform in an ETL pipeline?
How would you make a vague prompt more effective for an LLM?

[TAKEAWAY]
If you remember only one thing from today, always handle your errors explicitly.

[OUTRO]
That is your recap for class three. Read chapters 4 and 5 before Thursday.
You have got this. See you next session.
"""


class MockTranscript:
    class_name = "AI Consulting"
    date       = "April 24, 2026"
    instructor = "Prof. Sarah Kim"
    word_count = 120
    is_valid   = True
    error      = None
    clean_text = "Test content about APIs and ETL."


# ── Stage 1: data_processor ───────────────────────────────────────────────────

class TestDataProcessor:

    def test_load_from_string(self):
        result = load_transcript(SAMPLE)
        assert result.is_valid
        assert result.word_count > 20

    def test_load_from_file(self, tmp_path):
        f = tmp_path / "t.txt"
        f.write_text(SAMPLE)
        result = load_transcript(f)
        assert result.is_valid

    def test_metadata_class_name(self):
        assert _extract_metadata(SAMPLE)["class_name"] == "AI Consulting"

    def test_metadata_date(self):
        assert _extract_metadata(SAMPLE)["date"] == "April 24, 2026"

    def test_metadata_instructor(self):
        assert _extract_metadata(SAMPLE)["instructor"] == "Prof. Sarah Kim"

    def test_segments_count(self):
        segs = _parse_segments(SAMPLE)
        assert len(segs) == 4

    def test_segments_first_time(self):
        segs = _parse_segments(SAMPLE)
        assert segs[0]["time"] == "00:00"

    def test_clean_removes_timestamps(self):
        cleaned = _clean_text(SAMPLE)
        assert "[00:00]" not in cleaned
        assert "[05:00]" not in cleaned

    def test_clean_preserves_content(self):
        cleaned = _clean_text(SAMPLE)
        assert "APIs" in cleaned
        assert "ETL" in cleaned

    def test_too_short_returns_error(self):
        result = load_transcript("Too short.")
        assert not result.is_valid
        assert result.error is not None

    def test_empty_returns_error(self):
        result = load_transcript("")
        assert not result.is_valid

    def test_word_count_positive(self):
        result = load_transcript(SAMPLE)
        assert result.word_count > 0

    def test_is_valid_false_on_error(self):
        t = TranscriptData(raw_text="", clean_text="", error="test error")
        assert not t.is_valid

    def test_summary_contains_class_name(self):
        result = load_transcript(SAMPLE)
        assert "AI Consulting" in result.summary()


# ── Stage 2: llm_processor ───────────────────────────────────────────────────

class TestLlmProcessor:

    def test_extract_intro(self):
        intro = _extract_section(MOCK_LLM, "INTRO")
        assert "welcome" in intro.lower()

    def test_extract_overview(self):
        overview = _extract_section(MOCK_LLM, "OVERVIEW")
        assert "APIs" in overview or "ETL" in overview

    def test_extract_key_points(self):
        raw    = _extract_section(MOCK_LLM, "KEY POINTS")
        points = _parse_key_points(raw)
        assert len(points) >= 2

    def test_extract_quiz(self):
        raw       = _extract_section(MOCK_LLM, "QUIZ")
        questions = _parse_quiz(raw)
        assert len(questions) >= 2

    def test_extract_takeaway(self):
        takeaway = _extract_section(MOCK_LLM, "TAKEAWAY")
        assert "one thing" in takeaway.lower()

    def test_extract_outro(self):
        outro = _extract_section(MOCK_LLM, "OUTRO")
        assert outro != ""

    def test_assemble_script_has_transitions(self):
        script = _assemble_script(
            intro="Welcome back.",
            story_setup="Imagine no shared language.",
            overview="We covered APIs and ETL.",
            key_points=["REST APIs: explanation.", "ETL: explanation."],
            story_climax="Now everything connects.",
            deeper_dive="ETL is like a factory.",
            quiz_questions=["What is a 401?", "What is ETL?"],
            takeaway="Always handle errors.",
            outro="See you Thursday.",
        )
        assert "key concept" in script.lower()
        assert "deeper" in script.lower()

    def test_recap_script_valid(self):
        script = RecapScript(
            class_name  = "Test",
            date        = "2026-04-24",
            full_script = "Welcome back. Today we covered APIs.",
        )
        assert script.is_valid

    def test_recap_script_invalid_without_script(self):
        script = RecapScript(class_name="Test", date="2026-04-24")
        assert not script.is_valid

    def test_key_points_display(self):
        script = RecapScript(
            class_name  = "Test",
            date        = "2026-04-24",
            key_points  = ["Point A", "Point B"],
            full_script = "Full script here.",
        )
        display = script.key_points_display()
        assert "1. Point A" in display
        assert "2. Point B" in display

    def test_quiz_display(self):
        script = RecapScript(
            class_name     = "Test",
            date           = "2026-04-24",
            quiz_questions = ["Question one?", "Question two?"],
            full_script    = "Script.",
        )
        assert "Q1:" in script.quiz_display()
        assert "Q2:" in script.quiz_display()

    def test_invalid_transcript_propagates_error(self):
        from llm_processor import generate_recap

        class Bad:
            is_valid = False
            error    = "Intentional error"
            class_name = "Test"
            date = ""

        result = generate_recap(Bad())
        assert not result.is_valid
        assert "Intentional error" in result.error


# ── Stage 3: tts_generator ───────────────────────────────────────────────────

class TestTtsGenerator:

    def test_short_text_no_chunking(self):
        chunks = _chunk_text("Short sentence.", max_chars=500)
        assert len(chunks) == 1

    def test_long_text_splits_into_chunks(self):
        text   = "This is a sentence. " * 300
        chunks = _chunk_text(text, max_chars=1000)
        assert len(chunks) > 1

    def test_chunk_respects_limit(self):
        text   = "This is a sentence. " * 300
        chunks = _chunk_text(text, max_chars=1000)
        for chunk in chunks:
            assert len(chunk) < 1300

    def test_duration_estimate_format(self):
        est = _estimate_duration("word " * 140)
        assert "m" in est
        assert "s" in est

    def test_duration_short_text(self):
        est = _estimate_duration("Short.")
        assert "0m" in est

    def test_safe_filename_removes_special_chars(self):
        name = _safe_filename("AI & Consulting: Module #1!")
        assert "&" not in name
        assert "#" not in name
        assert "!" not in name

    def test_safe_filename_max_length(self):
        assert len(_safe_filename("a" * 100, max_len=40)) <= 40

    def test_audio_result_success_summary(self):
        r = AudioResult(success=True, file_path="output/test.mp3",
                        provider="openai", duration_estimate="~3m 0s")
        assert "✅" in r.summary()
        assert "test.mp3" in r.summary()

    def test_audio_result_failure_summary(self):
        r = AudioResult(success=False, error="API key missing")
        assert "❌" in r.summary()
        assert "API key missing" in r.summary()

    def test_generate_audio_invalid_script(self):
        from tts_generator import generate_audio

        class Bad:
            is_valid = False
            error    = "No script"

        result = generate_audio(Bad())
        assert not result.success
        assert "No script" in result.error


# ── Integration ───────────────────────────────────────────────────────────────

class TestIntegration:

    def test_stage1_produces_valid_transcript(self):
        t = load_transcript(SAMPLE)
        assert t.is_valid
        assert hasattr(t, "class_name")
        assert hasattr(t, "clean_text")
        assert hasattr(t, "word_count")

    def test_stage1_output_has_required_fields_for_stage2(self):
        t = load_transcript(SAMPLE)
        assert t.class_name != ""
        assert isinstance(t.segments, list)
        assert t.word_count > 0

    def test_stage2_output_has_required_fields_for_stage3(self):
        script = RecapScript(
            class_name  = "AI Consulting",
            date        = "April 24, 2026",
            full_script = "Welcome back. Today we covered APIs and ETL.",
        )
        assert script.is_valid
        assert callable(script.to_tts_text)
        tts = script.to_tts_text()
        assert isinstance(tts, str)
        assert len(tts) > 0

    def test_duration_estimate_on_realistic_script(self):
        script = RecapScript(
            class_name  = "Test",
            date        = "2026-04-24",
            full_script = "word " * 500,
        )
        est = _estimate_duration(script.to_tts_text())
        assert "m" in est
