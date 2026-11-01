# Paath Live

**Your material, taught step by step in your language.**

A teacher-led AI learning experience built around Sarvam AI for the **AI Innovation with Sarvam AI** hackathon.

Upload a chapter PDF, paste notes, or provide a topic outline. The teacher introduces the lesson, explains concepts aloud, works through examples on a simple visual board, asks the student questions, and adapts its explanation to the student's reasoning. The student can pause, ask a doubt, and resume the lesson.

**Status: two local services implemented: Lecture Studio processing and Paath Live source intake/review. The interactive teaching controller remains planned.**

## The demo we want

1. Supply a short, reviewed chapter on fractions and choose a teaching language.
2. The teacher starts the lesson and draws equal-sized fraction bars.
3. It asks whether 1/3 or 1/4 is larger.
4. The student says “1/4, because four is bigger.”
5. The teacher identifies that reasoning, changes its example and explains the equal-whole comparison.
6. It asks a fresh application question rather than declaring mastery.
7. The student pauses with a doubt, gets an answer, and resumes at the right lesson position.

The central contribution is the complete teaching loop: **teach → listen → check reasoning → repair → check again**. It should lead instruction proactively rather than require the student to prompt every explanation.

## MVP

- One student, one short source chapter, one tested Indian-language teaching path.
- PDF/text intake and a short lesson outline with source/page references where available.
- Short spoken teaching sections and a simple board for examples.
- Question checkpoints that wait for a student response.
- A different explanation when the student's reasoning reveals a misconception.
- Explicit pause/ask/resume, with stale audio cancelled.
- Standard Sarvam voice first; optional uploaded custom teacher voice through a separate speech adapter.

The teammate owns the recording-upload/custom-voice feature. It must remain independently buildable; the main teaching flow must work without it. See the [short teammate AI guide](docs/TEAMMATE-AI-GUIDE.md).

## Sarvam's role

| Capability | Proposed service |
|---|---|
| Understand student speech | Saaras speech-to-text |
| Plan, explain and assess answers | Sarvam 105B |
| Speak with a standard voice | Bulbul text-to-speech |
| Parse scanned/source PDFs when needed | Sarvam Document AI |
| Use an authorized uploaded voice sample | Optional Sarvam Instant Voice Cloning adapter, owned by teammate |

Sarvam can be the only AI provider. UI, source handling, lesson state, board rendering and playback control are ordinary application work. Exact account access, chosen model versions, latency and output quality need testing with credentials.

## Read before building

1. [Product details and scope](docs/PRODUCT.md)
2. [Architecture and integration boundary](docs/ARCHITECTURE.md)
3. [Short teammate AI guide](docs/TEAMMATE-AI-GUIDE.md)
4. [Demo and acceptance checklist](docs/DEMO-CHECKLIST.md)
5. [AI coding-agent instructions](AGENTS.md)
6. [Earlier feasibility research](research/LIVE-TEACHER-FEASIBILITY.md), retained as dated planning context; current documents take precedence.

## Start collaborating

Clone this repository, create a feature branch, and read `AGENTS.md`. There are no application install/run commands yet because no application has been scaffolded. Do not assume that the proposed routes or modules already exist.

Recommended starting stack: React + TypeScript frontend and Python/FastAPI backend. This is a planning choice; the main builder should confirm it in this document when scaffolding the app. Avoid introducing another framework for the voice-upload feature.

Copy `.env.example` to `.env` for server-side settings when implementation begins. Enter keys locally, never in tracked files or browser code. The checked-in environment example contains placeholders only.

## Scope after the hackathon core

Natural voice interruptions, larger curricula, class broadcasting, persistent student accounts and advanced board graphics can follow a working mini-lesson. A talking video avatar is unnecessary for the MVP.

## Evidence and sources

- [Sarvam tutor example](https://docs.sarvam.ai/api/cookbook/example-voice-agents/tutor-agent)
- [Sarvam EdTech guidance](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/use-cases/edtech)
- [Model catalog](https://docs.sarvam.ai/api/getting-started/models)
- [Document AI](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/overview)
- [Voice cloning overview](https://docs.sarvam.ai/api/api-guides-tutorials/voice-cloning/overview)

No learning-outcome, accuracy, novelty or performance claims have been measured. Demonstrate the implemented behavior and report actual test results.

## Run the integrated local services

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Set SARVAM_API_KEY locally in .env.
LECTURE_ENV_FILE="$PWD/.env" .venv/bin/python run_services.py
```

Requires FFmpeg on PATH. Lecture Studio runs at http://127.0.0.1:8765 and Paath Live at http://127.0.0.1:8766. Upload and process in Lecture Studio, then open Paath Live and import the chosen language. Imports are idempotent snapshots, marked `needs_review`, with the original timestamped transcript alongside generated notes. Importing does not use API credits.

Set `LECTURE_DATA_DIR` to an absolute existing jobs directory to reuse previous recordings. Defaults to `services/lecture-studio/jobs`. Credentials, recordings, imported sources and generated outputs are ignored by Git. Both services are loopback-only, single-user prototypes; no production authentication is implemented.

The existing notes generator still uses Sarvam. GPT/Gemini integration, diagram generation, MP4 export, learner assessment, custom voice and the interactive lesson controller are not implemented. Generated notes may contain factual/language errors and need review.
