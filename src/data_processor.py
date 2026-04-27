"""
src/data_processor.py
---------------------
Stage 1 — Transcript Ingestion

Accepts a class transcript from:
  - Pasted text (string)
  - Uploaded .txt file (file path from Gradio)

Returns a TranscriptData dataclass — the contract passed to llm_processor.py.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TranscriptData:
    raw_text:    str
    clean_text:  str
    class_name:  str        = "Unknown Class"
    date:        str        = ""
    instructor:  str        = ""
    word_count:  int        = 0
    segments:    list[dict] = field(default_factory=list)
    error:       Optional[str] = None

    def __post_init__(self):
        self.word_count = len(self.clean_text.split())

    @property
    def is_valid(self) -> bool:
        return bool(self.clean_text.strip()) and self.error is None

    def summary(self) -> str:
        parts = [self.class_name]
        if self.date:
            parts.append(self.date)
        parts.append(f"{self.word_count:,} words")
        parts.append(f"{len(self.segments)} segments")
        return " | ".join(parts)


_TIMESTAMP_RE  = re.compile(r"\[\d{1,2}:\d{2}(?::\d{2})?\]")
_HEADER_RE     = re.compile(r"^TRANSCRIPT\s*[—\-]?\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_DATE_RE       = re.compile(r"^Date:\s*(.+)$",                re.MULTILINE | re.IGNORECASE)
_INSTRUCTOR_RE = re.compile(r"^Instructor:\s*(.+)$",          re.MULTILINE | re.IGNORECASE)


def _extract_metadata(text: str) -> dict:
    meta = {"class_name": "Unknown Class", "date": "", "instructor": ""}
    m = _HEADER_RE.search(text)
    if m:
        meta["class_name"] = m.group(1).split("|")[0].strip()
    m = _DATE_RE.search(text)
    if m:
        meta["date"] = m.group(1).strip()
    m = _INSTRUCTOR_RE.search(text)
    if m:
        meta["instructor"] = m.group(1).strip()
    return meta


def _parse_segments(text: str) -> list[dict]:
    segments = []
    matches  = list(_TIMESTAMP_RE.finditer(text))
    for i, match in enumerate(matches):
        time_str = match.group().strip("[]")
        start    = match.end()
        end      = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        seg_text = text[start:end].strip()
        if seg_text:
            segments.append({"time": time_str, "text": seg_text})
    return segments


def _clean_text(text: str) -> str:
    lines       = text.strip().split("\n")
    content     = []
    past_header = False
    for line in lines:
        s = line.strip()
        if not past_header:
            skip = (
                re.match(r"^TRANSCRIPT", s, re.IGNORECASE)
                or re.match(r"^Date:",       s, re.IGNORECASE)
                or re.match(r"^Instructor:", s, re.IGNORECASE)
                or s == ""
            )
            if skip:
                continue
            past_header = True
        cleaned = _TIMESTAMP_RE.sub("", line).strip()
        if cleaned:
            content.append(cleaned)
    result = " ".join(content)
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result


def load_transcript(source: str | Path) -> TranscriptData:
    """
    Load and clean a class transcript from a file path or raw string.
    Returns TranscriptData ready for llm_processor.generate_recap()
    """
    source_str  = str(source)
    is_filepath = "\n" not in source_str and Path(source_str).exists()

    if is_filepath:
        logger.info("Loading from file: %s", source_str)
        try:
            raw_text = Path(source_str).read_text(encoding="utf-8")
        except Exception as exc:
            return TranscriptData(raw_text="", clean_text="",
                                  error=f"Cannot read file: {exc}")
    elif isinstance(source, str) and source.strip():
        logger.info("Loading from string (%d chars)", len(source))
        raw_text = source
    else:
        return TranscriptData(raw_text="", clean_text="",
                              error="No input provided.")

    if len(raw_text.strip()) < 100:
        return TranscriptData(
            raw_text=raw_text, clean_text="",
            error="Transcript too short. Paste the full class transcript."
        )

    meta     = _extract_metadata(raw_text)
    segments = _parse_segments(raw_text)
    clean    = _clean_text(raw_text)

    result = TranscriptData(
        raw_text   = raw_text,
        clean_text = clean,
        class_name = meta["class_name"],
        date       = meta["date"],
        instructor = meta["instructor"],
        segments   = segments,
    )
    logger.info("Loaded — %s", result.summary())
    return result