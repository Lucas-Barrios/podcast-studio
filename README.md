---
title: Recap Studio
emoji: 🎙️
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: "5.29.0"
python_version: "3.11"
app_file: app.py
pinned: false
---

# 🎙️ Recap Studio

> Transform any class transcript into a spoken podcast recap using AI.

Built for the **Ironhack AI & Integration Consulting** course — Module 1 Project.

---

## What It Does

Recap Studio takes a class transcript and turns it into a structured, spoken audio recap in under 2 minutes. Students can paste text, upload a PDF, or drop a URL and get back a podcast-style episode with key concepts, a deeper dive, self-test questions, and a clear takeaway.

### Pipeline

1. data_processor.py — cleans transcript, strips timestamps, extracts metadata
2. llm_processor.py — GPT-4o-mini generates structured script (Feynman + Story Arc)
3. tts_generator.py — OpenAI TTS converts script to MP3 (6 voice options)

---

## Key Features

- 3 input types — paste text, upload .txt or .pdf, or scrape a URL
- Feynman Method + Story Arc prompting — every concept explained in 3 layers
- 6 voice options — Nova, Shimmer, Alloy (female), Echo, Onyx, Fable (male)
- 3 tone options — Professional, Lively and Fun, Socratic
- Structured audio — Intro, Overview, Key Points, Deeper Dive, Self-Test, Takeaway, Outro
- Clean modern UI — built with Gradio, dark theme with purple accents

---

## Project Structure

    podcast-studio/
    src/
        data_processor.py    Stage 1 — ingest text, PDF, or URL
        llm_processor.py     Stage 2 — GPT-4o-mini generates script
        tts_generator.py     Stage 3 — OpenAI TTS generates audio
        main.py              Gradio web interface
    data/
        raw/                 Original transcripts
        processed/           Cleaned transcripts
    output/                  Generated audio files
    tests/
        test_pipeline.py     Unit tests for all 3 stages
    notebooks/               Jupyter notebooks
    docs/                    Documentation
    requirements.txt
    .env.example
    README.md

---

## Setup

### 1. Clone the repository

    git clone https://github.com/Lucas-Barrios/podcast-studio.git
    cd podcast-studio

### 2. Create and activate environment

    conda create -n podcast-studio python=3.11 -y
    conda activate podcast-studio

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Configure API keys

    cp .env.example .env

Open .env and add your key:

    OPENAI_API_KEY=your_openai_key_here

### 5. Run the app

    python src/main.py

Open http://localhost:7860

---

## How to Use

1. Open the app at http://localhost:7860
2. Choose your input — paste a transcript, upload a PDF, or enter a URL
3. Select a voice and a tone
4. Click Generate Recap Podcast
5. Wait 60 to 90 seconds for all 3 stages to complete
6. Listen to the audio, read the key points, and test yourself with the quiz

---

## Demo Audio

A sample output generated from the included class transcript is available here:

https://github.com/Lucas-Barrios/podcast-studio/raw/main/output/demo_recap.mp3

---

## API Costs

Service          | Model              | Cost per episode
OpenAI GPT-4o-mini | Script generation | 0.01 to 0.03 USD
OpenAI TTS       | tts-1, nova voice  | 0.02 to 0.05 USD
Total            |                    | 0.03 to 0.08 USD

---

## Run Tests

    pytest tests/ -v

---

## Tech Stack

Layer        | Technology
LLM          | OpenAI GPT-4o-mini
TTS          | OpenAI TTS tts-1
UI           | Gradio 6
PDF parsing  | PyPDF2
Web scraping | BeautifulSoup4
Language     | Python 3.11

---

## Use Case

Educational Recap — students upload or paste a class transcript and receive a spoken audio recap of 8 to 10 minutes, extracted key concepts, self-test quiz questions, and a one-sentence core takeaway. Built for bootcamp and university students who want to review material on the go.

---

Ironhack AI and Integration Consulting · Module 1 · April 2026
