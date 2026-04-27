"""
src/main.py — Recap Studio
"""

from __future__ import annotations
import logging, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from data_processor import load_transcript, load_url
from llm_processor  import generate_recap, TONE_OPTIONS
from tts_generator  import generate_audio, VOICE_OPTIONS, DEFAULT_VOICE

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)
SAMPLE_PATH = Path("data/raw/sample_transcript.txt")


def run_pipeline(transcript_text, transcript_file, url_input,
                 voice_label="Nova (Female, Warm)", tone_label="Professional"):
    voice = VOICE_OPTIONS.get(voice_label, DEFAULT_VOICE)
    tone  = TONE_OPTIONS.get(tone_label, "professional")

    if transcript_file is not None:
        source = transcript_file.name
    elif url_input.strip():
        yield "⏳ Fetching article...", "", "", "", None
        transcript = load_url(url_input.strip())
        if not transcript.is_valid:
            yield f"❌ {transcript.error}", "", "", "", None
            return
        yield f"✅ Loaded — {transcript.word_count:,} words\n⏳ Generating script...", "", "", "", None
        script = generate_recap(transcript, tone=tone)
        if not script.is_valid:
            yield f"❌ {script.error}", "", "", "", None
            return
        yield (f"✅ Loaded\n✅ Script ready — {len(script.key_points)} key points\n⏳ Generating audio...",
               script.key_points_display(), script.quiz_display(), _format_script(script), None)
        audio = generate_audio(script, voice=voice)
        msg = (f"✅ Loaded\n✅ Script ready\n✅ Audio ready — {audio.duration_estimate}\n\n🎙️ Podcast ready!"
               if audio.success else f"✅ Loaded\n✅ Script ready\n⚠️ Audio failed: {audio.error}")
        yield msg, script.key_points_display(), script.quiz_display(), _format_script(script), audio.file_path if audio.success else None
        return
    elif transcript_text.strip():
        source = transcript_text
    else:
        yield "❌ Please provide a transcript, file, or URL.", "", "", "", None
        return

    yield "⏳ Loading transcript...", "", "", "", None
    transcript = load_transcript(source)
    if not transcript.is_valid:
        yield f"❌ {transcript.error}", "", "", "", None
        return

    yield (f"✅ Loaded — {transcript.word_count:,} words · {transcript.class_name}\n⏳ Generating script with OpenAI...",
           "", "", "", None)
    script = generate_recap(transcript, tone=tone)
    if not script.is_valid:
        yield f"❌ {script.error}", "", "", "", None
        return

    yield (f"✅ Loaded — {transcript.word_count:,} words\n✅ Script ready — {len(script.key_points)} key points\n⏳ Generating audio...",
           script.key_points_display(), script.quiz_display(), _format_script(script), None)
    audio = generate_audio(script, voice=voice)
    if not audio.success:
        yield (f"✅ Loaded\n✅ Script ready\n⚠️ Audio failed — {audio.error}",
               script.key_points_display(), script.quiz_display(), _format_script(script), None)
        return
    yield (f"✅ Loaded — {transcript.word_count:,} words\n✅ Script ready — {len(script.key_points)} key points\n✅ Audio ready — {audio.duration_estimate} · {audio.provider.upper()}\n\n🎙️ Your recap podcast is ready!",
           script.key_points_display(), script.quiz_display(), _format_script(script), audio.file_path)


def _format_script(script):
    s = []
    if script.intro:       s.append(f"── INTRO ──\n{script.intro}")
    if script.overview:    s.append(f"── OVERVIEW ──\n{script.overview}")
    if script.key_points:  s.append("── KEY POINTS ──\n" + "\n\n".join(script.key_points))
    if script.deeper_dive: s.append(f"── DEEPER DIVE ──\n{script.deeper_dive}")
    if script.quiz_questions: s.append("── SELF-TEST ──\n" + "\n".join(script.quiz_questions))
    if script.takeaway:    s.append(f"── TAKEAWAY ──\n{script.takeaway}")
    if script.outro:       s.append(f"── OUTRO ──\n{script.outro}")
    return "\n\n".join(s)


def load_sample():
    return SAMPLE_PATH.read_text(encoding="utf-8") if SAMPLE_PATH.exists() else "Sample not found."


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .gradio-container {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background-color: #0e0e16 !important;
    color: #c9c7d4 !important;
}

.gradio-container { max-width: 100% !important; padding: 0 !important; }

/* ── Nuke ALL Gradio default borders and backgrounds ── */
.block, .gr-box, .gr-panel, .gr-form,
.wrap, .container, .gap, .padded,
.bordered, .gr-input-label, .gr-prose {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Topbar ── */
.rs-topbar {
    background: #0b0b12;
    border-bottom: 1px solid #1e1e30;
    padding: 0.8rem 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.rs-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.9rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
}
.rs-logo-dot {
    width: 9px; height: 9px;
    background: #8b5cf6;
    border-radius: 50%;
    box-shadow: 0 0 10px #8b5cf690;
}
.rs-topbar-right {
    font-size: 0.72rem;
    color: #44445a;
    font-weight: 400;
    letter-spacing: 0.02em;
}

/* ── Hero ── */
.rs-hero {
    text-align: center;
    padding: 4rem 2rem 2.5rem;
    position: relative;
}
.rs-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 300px;
    background: radial-gradient(ellipse at center, rgba(139,92,246,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.rs-hero h1 {
    font-size: 3.6rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -2.5px;
    line-height: 1.0;
    margin-bottom: 0.9rem;
}
.rs-hero h1 .accent { color: #8b5cf6; }
.rs-hero-sub {
    font-size: 1rem;
    color: #55556a;
    font-weight: 400;
    margin-bottom: 1.5rem;
    letter-spacing: -0.1px;
}
.rs-chips {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    flex-wrap: wrap;
}
.rs-chip {
    background: #13131e;
    border: 1px solid #22223a;
    border-radius: 100px;
    padding: 0.28rem 0.8rem;
    font-size: 0.72rem;
    font-weight: 600;
    color: #55556a;
    letter-spacing: 0.04em;
}
.rs-chip.purple {
    background: #1a1030;
    border-color: #3d2680;
    color: #a78bfa;
}

/* ── Main layout ── */
.rs-main {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 2rem 4rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
}

/* ── Card ── */
.rs-card {
    background: #13131e;
    border: 1px solid #1e1e30;
    border-radius: 16px;
    padding: 1.5rem;
}
.rs-card-title {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #44445a;
    margin-bottom: 0.75rem;
}

/* ── Section divider ── */
.rs-divider {
    border: none;
    border-top: 1px solid #1e1e30;
    margin: 1rem 0;
}

/* ── Labels ── */
label > span, .gr-form label span, label span {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #44445a !important;
}

/* ── Inputs & textareas ── */
textarea, input[type="text"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.93rem !important;
    font-weight: 400 !important;
    background: #0b0b14 !important;
    border: 1px solid #22223a !important;
    border-radius: 10px !important;
    color: #d0cfe0 !important;
    line-height: 1.65 !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    padding: 0.75rem 1rem !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
    outline: none !important;
}
textarea::placeholder, input::placeholder {
    color: #2e2e48 !important;
}

/* ── Select / Dropdown ── */
select {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    background: #0b0b14 !important;
    border: 1px solid #22223a !important;
    border-radius: 10px !important;
    color: #c0bfd0 !important;
    padding: 0.6rem 0.9rem !important;
}

/* ── Buttons ── */
button.primary {
    font-family: 'Inter', sans-serif !important;
    background: #8b5cf6 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.2px !important;
    padding: 0.85rem 2rem !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
button.primary:hover {
    background: #7c3aed !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(139,92,246,0.4) !important;
}
button.secondary {
    font-family: 'Inter', sans-serif !important;
    background: #13131e !important;
    color: #7070a0 !important;
    border: 1px solid #22223a !important;
    border-radius: 10px !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    transition: all 0.15s !important;
}
button.secondary:hover {
    background: #1a1a2e !important;
    color: #c0bfd0 !important;
    border-color: #3a3a58 !important;
}

/* ── File upload ── */
.gr-upload, .upload-btn-wrapper, [data-testid="upload-btn"] {
    background: #0b0b14 !important;
    border: 1px dashed #22223a !important;
    border-radius: 10px !important;
    color: #44445a !important;
}
.gr-upload:hover { border-color: #8b5cf6 !important; }

/* ── Tabs ── */
.gr-tab-nav, div[role="tablist"] {
    background: transparent !important;
    border-bottom: 1px solid #1e1e30 !important;
}
.gr-tab-nav button, div[role="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #44445a !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.5rem 0.9rem !important;
    letter-spacing: 0.01em !important;
}
.gr-tab-nav button.selected, div[role="tab"][aria-selected="true"] {
    color: #a78bfa !important;
    border-bottom-color: #8b5cf6 !important;
    background: transparent !important;
}

/* ── Status box ── */
.rs-status textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    line-height: 2 !important;
    color: #8888aa !important;
    background: #0b0b14 !important;
}

/* ── Audio player ── */
.gr-audio, [data-testid="audio"] {
    background: #0b0b14 !important;
    border: 1px solid #22223a !important;
    border-radius: 10px !important;
}

/* ── Pipeline steps ── */
.rs-steps {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 1rem;
    padding: 0.85rem 1.1rem;
    background: #0b0b14;
    border: 1px solid #1e1e30;
    border-radius: 10px;
}
.rs-step { display: flex; align-items: center; gap: 0.5rem; flex: 1; }
.rs-step-n {
    width: 22px; height: 22px;
    background: #1a1030;
    border: 1px solid #3d2680;
    border-radius: 6px;
    font-size: 0.62rem;
    font-weight: 800;
    color: #a78bfa;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.rs-step-t { font-size: 0.73rem; font-weight: 500; color: #44445a; }
.rs-step-sep { color: #22223a; font-size: 0.9rem; }

footer, .footer { display: none !important; }
"""


def build_ui():
    with gr.Blocks(title="Recap Studio", css=CSS) as demo:

        gr.HTML(f"""
        <div class="rs-topbar">
            <div class="rs-logo">
                <span class="rs-logo-dot"></span>
                Recap Studio
            </div>
            <div class="rs-topbar-right">GPT-4o-mini &nbsp;·&nbsp; OpenAI TTS &nbsp;·&nbsp; Feynman + Story Arc</div>
        </div>
        <div class="rs-hero">
            <h1>Turn any transcript<br>into a <span class="accent">podcast.</span></h1>
            <p class="rs-hero-sub">Paste a transcript, upload a PDF, or drop a URL — spoken audio recap in seconds</p>
            <div class="rs-chips">
                <span class="rs-chip purple">AI-Powered</span>
                <span class="rs-chip">3 input types</span>
                <span class="rs-chip">6 voices</span>
                <span class="rs-chip">3 tones</span>
                <span class="rs-chip">Feynman method</span>
            </div>
        </div>
        """)

        with gr.Row(equal_height=False):

            # ── LEFT ────────────────────────────────────────────────
            with gr.Column(scale=5):

                transcript_text = gr.Textbox(
                    label       = "Paste Transcript",
                    placeholder = "Paste your class transcript here...\n\nTip: add a header like:\nTRANSCRIPT — Course Name | Class N\nDate: April 24, 2026\nInstructor: Prof. Name",
                    lines       = 12,
                )
                with gr.Row():
                    sample_btn = gr.Button("Load Sample", variant="secondary", scale=1)
                    clear_btn  = gr.Button("Clear",       variant="secondary", scale=1)

                with gr.Row():
                    transcript_file = gr.File(
                        label="Upload (.txt or .pdf)",
                        file_types=[".txt", ".pdf"],
                        scale=1,
                    )
                    url_input = gr.Textbox(
                        label="Or Paste a URL",
                        placeholder="https://example.com/article",
                        lines=3,
                        scale=1,
                    )

                with gr.Row():
                    voice_dropdown = gr.Dropdown(
                        choices=list(VOICE_OPTIONS.keys()),
                        value="Nova (Female, Warm)",
                        label="Voice",
                        scale=1,
                    )
                    tone_dropdown = gr.Dropdown(
                        choices=list(TONE_OPTIONS.keys()),
                        value="Professional",
                        label="Tone",
                        scale=1,
                    )

                generate_btn = gr.Button("Generate Recap Podcast →", variant="primary", size="lg")

                gr.HTML("""
                <div class="rs-steps">
                    <div class="rs-step">
                        <div class="rs-step-n">01</div>
                        <span class="rs-step-t">Load & clean</span>
                    </div>
                    <span class="rs-step-sep">→</span>
                    <div class="rs-step">
                        <div class="rs-step-n">02</div>
                        <span class="rs-step-t">Generate script</span>
                    </div>
                    <span class="rs-step-sep">→</span>
                    <div class="rs-step">
                        <div class="rs-step-n">03</div>
                        <span class="rs-step-t">Synthesize audio</span>
                    </div>
                </div>
                """)

            # ── RIGHT ───────────────────────────────────────────────
            with gr.Column(scale=5):

                status_box = gr.Textbox(
                    label="Pipeline Status",
                    interactive=False,
                    lines=4,
                    placeholder="Status updates appear here...",
                    elem_classes=["rs-status"],
                )

                audio_out = gr.Audio(
                    label="Audio Output",
                    type="filepath",
                    interactive=False,
                )

                with gr.Tabs():
                    with gr.Tab("Key Points"):
                        key_points_box = gr.Textbox(
                            label="Extracted Concepts",
                            lines=8,
                            interactive=False,
                            placeholder="Key concepts appear after generation...",
                        )
                    with gr.Tab("Self-Test"):
                        quiz_box = gr.Textbox(
                            label="Quiz Questions",
                            lines=6,
                            interactive=False,
                            placeholder="Quiz questions appear after generation...",
                        )
                    with gr.Tab("Full Script"):
                        script_box = gr.Textbox(
                            label="Narration Script",
                            lines=15,
                            interactive=False,
                            placeholder="Full narration script appears after generation...",
                        )

        sample_btn.click(fn=load_sample, outputs=transcript_text)
        clear_btn.click(fn=lambda: ("", None, ""), outputs=[transcript_text, transcript_file, url_input])
        generate_btn.click(
            fn=run_pipeline,
            inputs=[transcript_text, transcript_file, url_input, voice_dropdown, tone_dropdown],
            outputs=[status_box, key_points_box, quiz_box, script_box, audio_out],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="0.0.0.0", server_port=7860)
