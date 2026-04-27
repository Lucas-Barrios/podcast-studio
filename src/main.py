"""
src/main.py
-----------
Entry point — Gradio web interface for the Educational Recap pipeline.

Pipeline:
  1. data_processor  -> load_transcript()  -> TranscriptData
  2. llm_processor   -> generate_recap()   -> RecapScript
  3. tts_generator   -> generate_audio()   -> AudioResult + MP3

Run:
    python src/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import gradio as gr

from data_processor import load_transcript, load_url
from llm_processor  import generate_recap
from tts_generator  import generate_audio

logging.basicConfig(
    level  = logging.INFO,
    format = "%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

SAMPLE_PATH = Path("data/raw/sample_transcript.txt")


def run_pipeline(transcript_text: str, transcript_file, url_input: str):
    if transcript_file is not None:
        source = transcript_file.name
    elif url_input.strip():
        yield "⏳ Stage 1 of 3 — Fetching article from URL...", "", "", "", None
        transcript = load_url(url_input.strip())
        if not transcript.is_valid:
            yield f"❌ Could not load URL: {transcript.error}", "", "", "", None
            return
        yield (
            f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n"
            f"   Source: {url_input.strip()[:60]}\n\n"
            f"⏳ Stage 2 of 3 — Generating recap script with OpenAI...",
            "", "", "", None
        )
        script = generate_recap(transcript)
        if not script.is_valid:
            yield f"❌ Script generation failed: {script.error}", "", "", "", None
            return
        yield (
            f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n\n"
            f"✅ Stage 2 complete — {len(script.key_points)} key points extracted\n\n"
            f"⏳ Stage 3 of 3 — Converting script to audio...",
            script.key_points_display(), script.quiz_display(), _format_script(script), None
        )
        audio = generate_audio(script)
        final_msg = (
            f"✅ Stage 1 complete — article fetched\n\n"
            f"✅ Stage 2 complete — {len(script.key_points)} key points extracted\n\n"
            f"✅ Stage 3 complete — Audio ready\n"
            f"   Duration: {audio.duration_estimate} | Provider: {audio.provider.upper()}\n\n"
            f"🎙️  Your recap podcast is ready!"
        ) if audio.success else f"✅ Stages 1 and 2 complete\n⚠️  Audio failed: {audio.error}"
        yield final_msg, script.key_points_display(), script.quiz_display(), _format_script(script), audio.file_path if audio.success else None
        return
    elif transcript_text.strip():
        source = transcript_text
    else:
        yield "❌ Please paste a transcript, upload a file, or enter a URL.", "", "", "", None
        return

    yield "⏳ Stage 1 of 3 — Loading transcript...", "", "", "", None
    transcript = load_transcript(source)
    if not transcript.is_valid:
        yield f"❌ Could not load transcript: {transcript.error}", "", "", "", None
        return

    yield (
        f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n"
        f"   Class: {transcript.class_name} | Date: {transcript.date}\n\n"
        f"⏳ Stage 2 of 3 — Generating recap script with OpenAI...",
        "", "", "", None
    )

    script = generate_recap(transcript)
    if not script.is_valid:
        yield f"❌ Script generation failed: {script.error}", "", "", "", None
        return

    yield (
        f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n"
        f"   Class: {transcript.class_name} | Date: {transcript.date}\n\n"
        f"✅ Stage 2 complete — {len(script.key_points)} key points extracted\n\n"
        f"⏳ Stage 3 of 3 — Converting script to audio...",
        script.key_points_display(),
        script.quiz_display(),
        _format_script(script),
        None,
    )

    audio = generate_audio(script)

    if not audio.success:
        yield (
            f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n"
            f"   Class: {transcript.class_name} | Date: {transcript.date}\n\n"
            f"✅ Stage 2 complete — {len(script.key_points)} key points extracted\n\n"
            f"⚠️  Stage 3 failed — {audio.error}\n"
            f"   Script is still available below.",
            script.key_points_display(),
            script.quiz_display(),
            _format_script(script),
            None,
        )
        return

    yield (
        f"✅ Stage 1 complete — {transcript.word_count:,} words loaded\n"
        f"   Class: {transcript.class_name} | Date: {transcript.date}\n\n"
        f"✅ Stage 2 complete — {len(script.key_points)} key points extracted\n\n"
        f"✅ Stage 3 complete — Audio ready\n"
        f"   Duration: {audio.duration_estimate} | Provider: {audio.provider.upper()}\n\n"
        f"🎙️  Your recap podcast is ready!",
        script.key_points_display(),
        script.quiz_display(),
        _format_script(script),
        audio.file_path,
    )


def _format_script(script) -> str:
    sections = []
    if script.intro:
        sections.append(f"── INTRO ──\n{script.intro}")
    if script.overview:
        sections.append(f"── OVERVIEW ──\n{script.overview}")
    if script.key_points:
        sections.append("── KEY POINTS ──\n" + "\n\n".join(script.key_points))
    if script.deeper_dive:
        sections.append(f"── DEEPER DIVE ──\n{script.deeper_dive}")
    if script.quiz_questions:
        sections.append("── SELF-TEST ──\n" + "\n".join(script.quiz_questions))
    if script.takeaway:
        sections.append(f"── TAKEAWAY ──\n{script.takeaway}")
    if script.outro:
        sections.append(f"── OUTRO ──\n{script.outro}")
    return "\n\n".join(sections)


def load_sample() -> str:
    if SAMPLE_PATH.exists():
        return SAMPLE_PATH.read_text(encoding="utf-8")
    return "Sample file not found at data/raw/sample_transcript.txt"


CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

body, .gradio-container {
    background: #f7f7f5 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.app-header {
    text-align: center;
    padding: 2.5rem 2rem 1.5rem;
    border-bottom: 1px solid #e8e8e4;
    margin-bottom: 2rem;
}
.app-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #1a1a1a;
    margin: 0 0 0.4rem;
    letter-spacing: -0.5px;
}
.app-header p {
    color: #6b6b6b;
    font-size: 1rem;
    font-weight: 300;
    margin: 0;
}
.app-header .badge {
    display: inline-block;
    background: #1a1a1a;
    color: #f7f7f5;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    padding: 0.25rem 0.75rem;
    border-radius: 2rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
}

.gr-group, .gr-box, .gr-panel {
    background: #ffffff !important;
    border: 1px solid #e8e8e4 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

label span {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #6b6b6b !important;
}

textarea, input[type="text"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
    border-color: #e8e8e4 !important;
    background: #fafaf8 !important;
    color: #1a1a1a !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #1a1a1a !important;
    box-shadow: 0 0 0 3px rgba(26,26,26,0.06) !important;
}

button.primary {
    background: #1a1a1a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}
button.primary:hover {
    background: #333333 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15) !important;
}

button.secondary {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #e8e8e4 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
button.secondary:hover {
    background: #f7f7f5 !important;
    border-color: #1a1a1a !important;
}

.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6b6b6b;
    margin: 0 0 0.5rem;
}

.divider {
    border: none;
    border-top: 1px solid #e8e8e4;
    margin: 1.25rem 0;
}

.status-box textarea {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    line-height: 1.7 !important;
    color: #3a3a3a !important;
}

.how-it-works {
    background: #ffffff;
    border: 1px solid #e8e8e4;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-top: 1.5rem;
}
.step {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.5rem 0;
}
.step-num {
    background: #1a1a1a;
    color: white;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 2px;
}
.step p {
    font-size: 0.85rem;
    color: #6b6b6b;
    margin: 0;
    line-height: 1.6;
}

footer { display: none !important; }
"""


def build_ui() -> gr.Blocks:

    with gr.Blocks(title="Recap Studio") as demo:

        gr.HTML("""
        <div class="app-header">
            <div class="badge">AI-Powered Education</div>
            <h1>🎙 Recap Studio</h1>
            <p>Transform any class transcript into a spoken podcast recap in seconds</p>
        </div>
        """)

        with gr.Row(equal_height=False):

            with gr.Column(scale=1):
                gr.HTML('<p class="section-label">📥 Paste Transcript</p>')
                transcript_text = gr.Textbox(
                    label       = "",
                    placeholder = "Paste your class transcript here...\n\nTip: add a header like:\nTRANSCRIPT — Course Name | Class N\nDate: April 24, 2026\nInstructor: Prof. Name",
                    lines       = 14,
                )
                with gr.Row():
                    sample_btn = gr.Button("Load Sample", variant="secondary", scale=1)
                    clear_btn  = gr.Button("Clear",       variant="secondary", scale=1)

                gr.HTML('<hr class="divider"><p class="section-label">📎 Upload File (.txt or .pdf)</p>')
                transcript_file = gr.File(
                    label      = "",
                    file_types = [".txt", ".pdf"],
                )

                gr.HTML('<hr class="divider"><p class="section-label">🔗 Or Paste a URL</p>')
                url_input = gr.Textbox(
                    label       = "",
                    placeholder = "https://example.com/article",
                    lines       = 1,
                )

                gr.HTML('<hr class="divider">')
                generate_btn = gr.Button(
                    "Generate Recap Podcast →",
                    variant = "primary",
                    size    = "lg",
                )

            with gr.Column(scale=1):
                gr.HTML('<p class="section-label">📊 Pipeline Status</p>')
                status_box = gr.Textbox(
                    label        = "",
                    interactive  = False,
                    lines        = 6,
                    placeholder  = "Status updates appear here...",
                    elem_classes = ["status-box"],
                )

                gr.HTML('<hr class="divider"><p class="section-label">🔊 Audio Output</p>')
                audio_out = gr.Audio(
                    label       = "",
                    type        = "filepath",
                    interactive = False,
                )

                gr.HTML('<hr class="divider"><p class="section-label">📋 Generated Content</p>')
                with gr.Tabs():
                    with gr.Tab("Key Points"):
                        key_points_box = gr.Textbox(
                            label       = "",
                            lines       = 8,
                            interactive = False,
                            placeholder = "Key concepts extracted from the transcript...",
                        )
                    with gr.Tab("Self-Test"):
                        quiz_box = gr.Textbox(
                            label       = "",
                            lines       = 6,
                            interactive = False,
                            placeholder = "Quiz questions to test your understanding...",
                        )
                    with gr.Tab("Full Script"):
                        script_box = gr.Textbox(
                            label       = "",
                            lines       = 18,
                            interactive = False,
                            placeholder = "The full narration script...",
                        )

        gr.HTML("""
        <div class="how-it-works">
            <p class="section-label" style="color:#1a1a1a; margin-bottom:0.75rem;">How it works</p>
            <div class="step">
                <div class="step-num">1</div>
                <p><strong>data_processor.py</strong> — loads your transcript, strips timestamps, handles PDF and URL sources</p>
            </div>
            <div class="step">
                <div class="step-num">2</div>
                <p><strong>llm_processor.py</strong> — sends to GPT-4o-mini with Feynman + Story Arc prompting, builds structured script</p>
            </div>
            <div class="step">
                <div class="step-num">3</div>
                <p><strong>tts_generator.py</strong> — converts script to MP3 via OpenAI TTS (nova voice)</p>
            </div>
        </div>
        """)

        sample_btn.click(fn=load_sample, outputs=transcript_text)
        clear_btn.click(fn=lambda: ("", None, ""), outputs=[transcript_text, transcript_file, url_input])
        generate_btn.click(
            fn      = run_pipeline,
            inputs  = [transcript_text, transcript_file, url_input],
            outputs = [status_box, key_points_box, quiz_box, script_box, audio_out],
        )

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(
        server_name = "0.0.0.0",
        server_port = 7860,
        show_error  = True,
        css         = CSS,
    )
