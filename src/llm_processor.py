"""
src/llm_processor.py
--------------------
Stage 2 — Script Generation

Transforms a TranscriptData into a structured RecapScript using Claude.
Returns a RecapScript dataclass — the contract passed to tts_generator.py.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RecapScript:
    class_name:     str
    date:           str
    intro:          str           = ""
    overview:       str           = ""
    key_points:     list[str]     = field(default_factory=list)
    deeper_dive:    str           = ""
    quiz_questions: list[str]     = field(default_factory=list)
    takeaway:       str           = ""
    outro:          str           = ""
    full_script:    str           = ""
    error:          Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return bool(self.full_script.strip()) and self.error is None

    def to_tts_text(self) -> str:
        return self.full_script

    def key_points_display(self) -> str:
        if not self.key_points:
            return "No key points extracted."
        return "\n".join(f"{i}. {pt}" for i, pt in enumerate(self.key_points, 1))

    def quiz_display(self) -> str:
        if not self.quiz_questions:
            return ""
        return "\n".join(f"Q{i}: {q}" for i, q in enumerate(self.quiz_questions, 1))


_SYSTEM_PROMPT = """\
You are an expert educational podcast host — a brilliant teaching assistant
who turns any lecture into a crisp, engaging audio review.

Your voice is:
- Warm and encouraging, like a study buddy who actually paid attention
- Direct and efficient — students are busy, no padding
- Concrete — always use examples, analogies, real-world connections
- Spoken — every sentence must sound natural out loud

You are producing a WORD-FOR-WORD SCRIPT that a narrator reads into a microphone.
There is no visual component. Make every concept land through sound alone.\
"""


def _build_prompt(transcript) -> str:
    return f"""\
Transform this class transcript into an educational audio recap podcast script.

CONTEXT:
- Course: {transcript.class_name}
- Date: {transcript.date}
- Instructor: {transcript.instructor}
- Length: {transcript.word_count:,} words

TRANSCRIPT:
{transcript.clean_text[:14000]}

---

OUTPUT FORMAT — produce each section with its label in square brackets.
Write ONLY the spoken words. No markdown, no bullet symbols.

[INTRO]
2 sentences. Open with energy. Name the course and date.

[OVERVIEW]
1-2 sentences. State the main topics covered. This is the roadmap.

[KEY POINTS]
Exactly 3 to 5 key concepts. Each on its own line.
Format: CONCEPT NAME: one sentence explaining it. One sentence on why it matters.

[DEEPER DIVE]
3-4 paragraphs on the single most important concept.
Name it clearly. Use one analogy. Connect it to something students will build.

[QUIZ]
Exactly 2 self-test questions that check real understanding.
One question per line.

[TAKEAWAY]
One sentence. The core lesson.
Start with: "If you remember only one thing from today..."

[OUTRO]
2 sentences. Warm close. Mention what is coming next if possible.

---
Total target: 3 to 4 minutes spoken (450 to 600 words).
Plain spoken English only. No markdown.\
"""


def _extract_section(text: str, section: str) -> str:
    pattern = rf"\[{section}\](.*?)(?=\[[A-Z ]+\]|$)"
    match   = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_key_points(raw: str) -> list[str]:
    points = []
    for line in raw.split("\n"):
        line = line.strip().lstrip("•-–*0123456789.) ").strip()
        if len(line) > 10:
            points.append(line)
    return points


def _parse_quiz(raw: str) -> list[str]:
    questions = []
    for line in raw.split("\n"):
        line = line.strip().lstrip("Q0123456789.: ").strip()
        if line.endswith("?") or len(line) > 20:
            questions.append(line)
    return questions[:2]


def _assemble_script(intro, overview, key_points, deeper_dive,
                     quiz_questions, takeaway, outro) -> str:
    parts = []
    if intro:
        parts.append(intro)
    if overview:
        parts.append(overview)
    if key_points:
        parts.append("Let's walk through the key concepts.")
        for point in key_points:
            parts.append(point)
    if deeper_dive:
        parts.append("Now let's go deeper on the most important idea from today.")
        parts.append(deeper_dive)
    if quiz_questions:
        parts.append(
            "Before we wrap up, here are two quick questions to test yourself. "
            "Pause and think about each one."
        )
        for q in quiz_questions:
            parts.append(q)
    if takeaway:
        parts.append(takeaway)
    if outro:
        parts.append(outro)
    return "\n\n".join(filter(None, parts))


def _parse_response(raw: str, transcript) -> RecapScript:
    intro          = _extract_section(raw, "INTRO")
    overview       = _extract_section(raw, "OVERVIEW")
    key_points     = _parse_key_points(_extract_section(raw, "KEY POINTS"))
    deeper_dive    = _extract_section(raw, "DEEPER DIVE")
    quiz_questions = _parse_quiz(_extract_section(raw, "QUIZ"))
    takeaway       = _extract_section(raw, "TAKEAWAY")
    outro          = _extract_section(raw, "OUTRO")

    full_script = _assemble_script(
        intro, overview, key_points, deeper_dive,
        quiz_questions, takeaway, outro
    )

    if not full_script.strip():
        full_script = raw

    return RecapScript(
        class_name     = transcript.class_name,
        date           = transcript.date,
        intro          = intro,
        overview       = overview,
        key_points     = key_points,
        deeper_dive    = deeper_dive,
        quiz_questions = quiz_questions,
        takeaway       = takeaway,
        outro          = outro,
        full_script    = full_script,
    )


def _call_claude(prompt: str) -> str:
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")
    client  = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model      = "claude-opus-4-5",
        max_tokens = 2048,
        system     = _SYSTEM_PROMPT,
        messages   = [{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def generate_recap(transcript) -> RecapScript:
    """
    Transform a TranscriptData into a RecapScript using Claude.
    Returns RecapScript with structured sections and TTS-ready full_script.
    """
    if not transcript.is_valid:
        return RecapScript(
            class_name = transcript.class_name,
            date       = transcript.date,
            error      = transcript.error or "Invalid transcript.",
        )

    logger.info("Generating recap for: %s", transcript.class_name)

    try:
        prompt = _build_prompt(transcript)
        raw    = _call_claude(prompt)
        script = _parse_response(raw, transcript)
        logger.info(
            "Recap ready — %d key points, %d quiz questions, %d chars",
            len(script.key_points), len(script.quiz_questions), len(script.full_script)
        )
        return script

    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return RecapScript(
            class_name = transcript.class_name,
            date       = transcript.date,
            error      = str(exc),
        )