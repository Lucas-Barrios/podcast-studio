#!/bin/bash
cp src/main.py app.py

python - << 'PYEOF'
with open('app.py', 'r') as f:
    content = f.read()
content = content.replace(
    "sys.path.insert(0, str(Path(__file__).parent))",
    "sys.path.insert(0, str(Path(__file__).parent))\nsys.path.insert(0, str(Path(__file__).parent / 'src'))"
)
content = content.replace(
    'build_ui().launch(server_name="0.0.0.0", server_port=7860, show_error=True, css=CSS, share=True)',
    'build_ui().launch(server_name="0.0.0.0", server_port=7860, show_error=True)'
)
content = content.replace(
    'with gr.Blocks(title="Learncast") as demo:',
    'with gr.Blocks(title="Learncast", css=CSS) as demo:'
)
content = content.replace(
    'def run_pipeline(transcript_text, transcript_file, url_input,\n                 voice_label="Nova (Female, Warm)", tone_label="Professional"):',
    'def run_pipeline(transcript_text, transcript_file, url_input,\n                 voice_label="Nova (Female, Warm)", tone_label="Professional",\n                 mode_label="Deep Dive (~8 min)"):'
)
content = content.replace(
    '    voice = VOICE_OPTIONS.get(voice_label, DEFAULT_VOICE)\n    tone  = TONE_OPTIONS.get(tone_label, "professional")',
    '    voice = VOICE_OPTIONS.get(voice_label, DEFAULT_VOICE)\n    tone  = TONE_OPTIONS.get(tone_label, "professional")\n    mode  = "quick" if "Quick" in mode_label else "deep"'
)
with open('app.py', 'w') as f:
    f.write(content)
print("app.py synced successfully")
PYEOF
