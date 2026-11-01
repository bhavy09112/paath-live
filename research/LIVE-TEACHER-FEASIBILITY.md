# Live teacher with Sarvam: feasibility and hackathon scope

Updated 1 November 2026. Theme: AI innovation with Sarvam AI. User clarification: the agent leads the teaching of supplied material like a teacher, rather than merely answering questions. The reported remaining time is “1.2 hour”; this plan conservatively targets roughly 60–75 minutes. No API requests, prototype implementation or learner trials have been performed.

## Decision

Proceed with a small teacher-led, one-student lesson. Sarvam can be the only AI provider. Ordinary application code must handle the lesson sequence, source references, audio playback, pauses and learner state. A separate AI subscription is not inherently necessary.

Recommended working concept: **Paath Live — your material, taught step by step in your language.**

The agent proactively introduces the topic, explains a short section, displays an example, asks a meaningful question, waits for the student, and chooses the next explanation from the answer. It resumes the lesson after handling a doubt. A generic conversation prompt alone will not reliably enforce this behavior.

## Verified capability map

| Need | Sarvam capability | Additional application work |
|---|---|---|
| Read a digital/scanned PDF | Document AI parse with Sarvam Vision | Submit/poll job, retain page provenance, review extraction quality |
| Plan and teach | Sarvam 105B | Source selection, lesson state and structured response validation |
| Understand student speech | Saaras speech-to-text | Capture/encode audio; show transcript so misrecognition can be corrected |
| Speak the lesson | Bulbul text-to-speech | Play short segments; manage cancellation, pause and resume |
| Explain in an Indian language | LLM plus translation where useful | Explicit language selection; validate supported model/voice combination |
| Show board content | LLM proposes text/structured board steps | Render using ordinary HTML, SVG and math formatting; no video generator required |
| Follow the lesson autonomously | Not an API feature on its own | A deterministic lesson controller |

Sources: [Sarvam models](https://docs.sarvam.ai/api/getting-started/models), [Document AI](https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/overview), [chat completion](https://docs.sarvam.ai/api/token-factory/chat-completions).

Sarvam publishes a [Pipecat tutor example](https://docs.sarvam.ai/api/cookbook/example-voice-agents/tutor-agent). Its [EdTech guide](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/use-cases/edtech) recommends trusted content, paced explanations and checks for understanding. This supports feasibility, but a basic multilingual tutor is already a documented use case. The demo must show the quality of the teaching interaction.

## Minimum versus expanded stack

### Minimum for this time budget

- One web interface and one backend process.
- Sarvam API access for LLM, STT and TTS; Document AI if scanned PDF support is retained.
- Local text-PDF extraction for a simple digital PDF, or supplied text as a visible fallback. This is ordinary software, not another AI provider.
- A small in-memory lesson outline and page-tagged source excerpts; no embedding service or vector database needed for a short chapter.
- A simple board with a few supported layouts, plus speech playback.
- A “Pause and ask” button: stop the teacher immediately, capture the student’s short question, answer it, and resume at the recorded position.

Synchronous STT has a 30-second limit per request, so the simplest version needs short student turns. [Speech REST documentation](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/rest-api)

### If adding natural spoken interruptions later

Choose one real-time framework, rather than combining two:

- **LiveKit + Sarvam:** Sarvam documents a working integration; its Cloud path requires LiveKit credentials in addition to Sarvam. [Integration guide](https://docs.sarvam.ai/api/integration/build-voice-agent-with-live-kit)
- **Pipecat + Sarvam + SmallWebRTC:** Pipecat documents a browser-to-server transport that needs no third-party transport account. Remote deployment can still require networking/TURN and hosting work. [Transport choices](https://docs.pipecat.ai/client/concepts/choosing-a-transport)

Interruption handling includes endpointing, cancelling old generation, stopping queued audio and remembering only what was actually played. [LiveKit turn handling](https://docs.livekit.io/agents/logic/turns/)

These are infrastructure choices. They do not require replacing Sarvam with a second LLM, speech recognizer or voice model. Under the current deadline, a reliable button-based interruption is the preferred first version.

### Expansion beyond the hackathon core

A whole class adds participant identity, floor control, shared timing, teacher moderation and private learner checks. A realistic talking avatar adds a separate rendering/animation component and synchronization work. Arbitrary generated videos, unconstrained live diagrams, broad curriculum coverage and persistent student analytics each add separate failure modes. They are not needed to establish the proposed teaching loop.

## Material versus topic list

- **Chapter PDF or notes:** extract, attach page/source IDs, and teach from those excerpts. Keep a bounded source size and document the unsupported formats.
- **Scanned PDF:** OCR is possible through Document AI, but extraction is an asynchronous preparation step. Do not claim the lesson starts before processing finishes.
- **Topic list:** it establishes scope, not authoritative facts, examples or grade level. Show an outline for review and label model-generated material; use trusted supplied content for the judged demo.
- **Diagrams and equations:** extracted text alone may lose structure. Start with a legible chapter and review its important examples. Broad diagram interpretation is not a safe assumption.

## Teacher-led control loop

```text
Prepare source and outline
  -> introduce lesson goal
  -> ask one short diagnostic/prediction question
  -> wait for learner
  -> explain one connected step + display example
  -> ask an application question
  -> wait for learner
  -> inspect answer and reasoning
     -> sound reasoning: next step
     -> misconception: targeted repair + new check
     -> unclear transcript: clarify, do not grade
  -> brief recap and evidence of what remains uncertain
```

While an explanation is being played, completion of audio triggers the next planned event. A checkpoint requires an actual learner response or an explicit “continue” choice; silence is not correctness. An “I have a doubt” event saves the lesson position and stops old audio before a new response starts. Increment a response/version ID so a late API response cannot resume cancelled speech.

The LearnHarness teaching skill informed the distinction between explanation, prediction and assessment. This is a proposed teaching design, not evidence of learning efficacy. Do not label a concept mastered from listening, a guessed answer or a self-reported “yes, understood.”

## Fifteen feature ideas through three lenses

Product lens:

1. Teacher-led chapter mini-lesson.
2. Brief prerequisite diagnosis before the lesson.
3. Wrong-answer repair tied to a specific misconception.
4. Exam revision focused on gaps observed in answers.
5. Teacher-facing summary of responses and remaining uncertainty.

Designer lens:

6. Visible board updates alongside short spoken sections.
7. Pause/ask/resume with a visible lesson position.
8. Explain again using a different concrete example.
9. Display the source page for each planned section.
10. Let students answer in their preferred language while retaining technical vocabulary.

Engineering lens:

11. Structured lesson events validated against a schema.
12. Playback-aware lesson sequencing with stale-response cancellation.
13. Short-chapter context selection without a vector database.
14. Optional streaming voice with natural barge-in.
15. Exact arithmetic or symbolic verification for a limited supported problem type.

## Top five features for the demo

| Rank | Feature | Why prioritize | Key assumption to test |
|---|---|---|---|
| 1 | Proactive short lesson from supplied material | Delivers the user's central idea | The agent can lead coherent sections without repeated student prompts |
| 2 | Diagnose, explain, check, repair | Creates an observable teaching adaptation | It identifies the reasoning error rather than simply repeating the explanation |
| 3 | Pause, ask and resume | Makes the session feel live | Cancelling speech and restoring the correct position works reliably |
| 4 | Simple board with examples and source page | Makes spoken instruction inspectable | Board and speech stay aligned at section level |
| 5 | One Indian-language teaching path | Makes Sarvam integral and keeps quality review feasible | A fluent reviewer understands both instruction and readback |

Use a weighted decision matrix based on core value, validation speed and differentiation rather than invented market data. The top-five ranking is a design judgment. Natural automatic interruption, avatar video, multiple users and a full syllabus are lower priority under the deadline.

## Competitive reality

| Product/source | Verified overlap | Consequence |
|---|---|---|
| [Sarvam tutor example](https://docs.sarvam.ai/api/cookbook/example-voice-agents/tutor-agent) | Multilingual voice tutoring and adaptive explanations | API assembly alone is insufficient distinction |
| [StudyFetch Tutor Me](https://sso.studyfetch.com/docs/docs/account-support/tutor-me-vs-spark-e-chat) | Speaking tutor leads one-to-one instruction and checks understanding | Do not claim teacher-led material tutoring is new |
| [Google source-based Audio Overviews](https://support.google.com/gemininotebook/answer/16212820?hl=en) | Uploaded-source audio and interactive questions; consulted documentation limits interactive mode to English | A regional-language demonstration is relevant, but not proof of exclusivity |
| [Khanmigo](https://www.khanacademy.org/khan-labs) | Tutoring and learning support | Show actual handling of student reasoning |
| [Leoki](https://www.leoki.ai/) | Advertises multilingual voice-first learning and classroom use | “AI teacher in Indian languages” is an existing category |

These are advertised features, not independently tested comparative performance. Position the hackathon entry around a demonstrated lesson repair with source evidence. Do not claim first, uniquely adaptive or superior learning outcomes without evidence.

## Best demo

Use a short reviewed chapter on fractions. The teacher introduces a concept, draws fraction bars and asks the student to compare 1/4 with 1/3. The student argues that 1/4 is larger because 4 is larger than 3. The teacher returns to equal-sized wholes, changes the board to equal-whole fraction bars, explains why more equal pieces means smaller pieces, then asks a new transfer question: compare 1/5 and 1/2.

The intended judge-visible result is a specific changed explanation followed by a new application question. Whether a real learner improves must be measured. Avoid displaying a fabricated mastery score.

Use one lesson, one language path and one clearly working doubt interruption. Board drawings can be deterministic templates selected by structured events. They do not need generative video or unrestricted generated code.

## Timebox and cut rules

Proposed 70-minute budget, assuming an available development environment and working credentials; this is not a delivery guarantee:

- Minutes 0–10: prove one real LLM, speech input and speech output request; choose the content and language.
- Minutes 10–25: source text, outline and lesson-state controller; accept pasted text if PDF processing is not ready.
- Minutes 25–40: short lesson sections and one visual board template.
- Minutes 40–50: answer evaluation, one misconception repair and pause/resume.
- Minutes 50–60: source labels, error recovery and honest progress display.
- Minutes 60–70: rehearse the full three-minute demo on the actual browser; fix blocking failures only.

If speech capture fails, retain typed learner answers while still using Sarvam speech output. If PDF ingestion fails, use pasted source text visibly; do not pretend a file was parsed. If the main loop is not reliable, cut to the oral teach-back variant below. Preserve rehearsal time.

## Smaller variants if the full lesson loop slips

1. **Explain-back tutor:** explain one concept, hear the student explain it back, identify one error, repair and recheck. Recommended smallest alternative.
2. **Regional-language oral viva:** ask chapter-grounded questions, give hints and explain the answer after the attempt. Easier turn control; requires showing an educational benefit beyond quiz generation.
3. **Teacher's live lesson assistant:** show a source-grounded explanation and board for a human teacher to advance. Less autonomous, with simpler classroom control.

These preserve the education direction; a pivot to an unrelated product would consume the remaining time.

## Assumptions and fast tests

| Category | Unproven assumption | Fast check |
|---|---|---|
| Value | Students need this lesson format | Ask two relevant learners about the last concept they could not understand from their notes |
| Usability | Learners know when to listen, answer and interrupt | Observe an uncoached peer completing the mini-lesson |
| Viability | Session cost is acceptable to a future buyer | Measure actual tokens, speech seconds and characters; willingness to pay remains unknown |
| Feasibility | Sarvam outputs work quickly enough on the actual account | Test the chosen model/voice and source with credentials before polishing |
| Ethics | The tutor avoids teaching incorrect content as fact | Review lesson/examples; keep sources visible and transcript ambiguities out of grading |
| Go-to-market | A teacher or class will try it | Ask for one concrete trial after the demo |
| Strategy | The local-language repair demo is compelling despite competitors | Ask a reviewer to describe what the app changed after the wrong answer |
| Team | The remaining work fits the clock | Cut at the stated gates; keep one lesson and one language |

Proposed experiments, not results:

1. At least 2 of 3 peers complete the mini-lesson and submit an answer without facilitator help. Record intervention count and failure point.
2. On five reviewed correct/incorrect/unclear responses, the tutor gives appropriate feedback and never marks unclear transcription as a conceptual error. Any factually wrong repair blocks that demo content.
3. At least 1 of 2 relevant learners or educators commits to a later session with their own material. Praise alone is not demand evidence.

## Plugin Management check

The requested Plugin Management skill and plugin were used to search for Sarvam and LiveKit integrations. Neither exact search returned a matching plugin in the available directory. A broader research search returned unrelated or optional products, none necessary for this feasibility assessment. No plugin was installed or connected. Directory results are not exhaustive. The future application can integrate the published APIs and libraries directly; Codex plugins are not application runtime dependencies.

## Completion boundary

This document establishes documented capability, a bounded architecture and an idea-stage test plan. It does not establish actual API latency, PDF accuracy, teaching correctness, student learning gains or a finished application. The recommendation replaces the earlier commerce concept for the user's current education direction.
