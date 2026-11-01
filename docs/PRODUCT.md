# Product brief

## Goal

Turn a learner's supplied material into an interactive, teacher-led mini-lesson delivered in their preferred supported Indian language. The teacher takes initiative, works through concepts and examples, and responds to the student's reasoning.

Primary user hypothesis: a learner who has notes or a chapter but needs spoken explanations and help at a specific conceptual gap. The initial demo can use a school-level fractions lesson; broader subject coverage is not assumed.

## Input modes

- **Short digital PDF:** extract text, preserve pages and prepare the lesson.
- **Scanned PDF:** use Sarvam Document AI and wait for processing before teaching.
- **Pasted notes:** fastest reliable fallback, clearly identified as pasted source.
- **Topic list:** defines scope but not authoritative content. Generate an outline for review and distinguish model-created material from source-grounded explanation.

Start with a reviewed chapter and a known teaching language. Grade level and the learner's goal should be explicit session context.

## Learning experience

1. Prepare a short outline with source references and one lesson goal.
2. Introduce the goal and ask a short diagnostic or prediction question where useful.
3. Explain one connected idea aloud while displaying a relevant example.
4. Ask one application question, then wait.
5. Inspect the answer and reasoning. Correct reasoning advances the lesson; a misconception gets a targeted explanation and a new check.
6. Handle a doubt without losing the lesson position.
7. End with a recap of what was explained, what the student applied and what remains uncertain.

Explanations and checks are distinct turns. Silence is not a correct answer. A correct number with incorrect reasoning is not a clean success. Unclear speech recognition needs clarification before assessment.

## Custom teacher voice: teammate-owned extension

A user can optionally upload a short authorized reference recording and select the resulting voice for the teacher. The selected voice changes speech synthesis, not lesson planning, student assessment or source content. It does not train the teacher's subject knowledge.

Assumption: “use the recording for our teacher” means synthesizing new lesson speech with that voice. If the desired feature is instead transcription of a recorded lecture, that is a separate source-intake mode and should be agreed before implementation.

The standard voice remains available. The UI must accurately show the voice currently in use. Failed custom voice generation must not silently masquerade as successful custom synthesis.

## Hackathon boundaries

Include one complete lesson, a simple board, one language path, learner answers, one adaptive repair and pause/ask/resume. Treat custom voice as a parallel extension behind a shared interface.

Defer class broadcasting, a photoreal avatar, automatic open-domain research, unrestricted generated diagrams, persistent learning profiles and long curricula. Exact build time depends on the team's environment and provider access.

## Why the demo could be compelling

The observable moment is the tutor changing its explanation after a specific wrong reason, then asking a new transfer question. Regional-language speech makes Sarvam central. Uploaded custom voice adds personalization without changing the pedagogical core.

Existing products and Sarvam's own cookbook already offer voice tutoring. Do not claim the category is new. User demand, teaching quality and any learning improvement remain hypotheses until tested.
