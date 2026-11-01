# Proposed architecture and shared boundary

**Implementation update:** the core is being built in `backend/main.py` and `frontend/`. Gemini Flash replaces Sarvam 105B for planning, feedback and doubts; Sarvam handles speech. `/api/speech` is the implemented synthesis boundary. Custom selections remain unimplemented and return 501. Inspect current code before applying the proposed extension routes below.

## Core flow

```text
PDF / pasted notes / topic outline
  -> source preparation with provenance
  -> short lesson plan
  -> lesson controller
       -> explanation + board event
       -> speech provider -> playable audio
       -> wait for student
       -> typed answer or Saaras transcript
       -> evaluate reasoning -> repair / next concept
```

The controller, not the LLM alone, owns the lesson position and whether student input is required. Advance after playback completion only if the current event permits it. Stop at question checkpoints. Track `session_id`, `lesson_step_id` and `response_version`; reject stale results after pause, interruption or a changed answer.

Source identifiers and page references must come from actual extraction metadata. Display board content section by section; word-perfect audio alignment is outside the first version.

## Speech seam: main builder and teammate

All teacher speech goes through one service. Its provider can be the standard Bulbul adapter or the teammate's custom-voice adapter. Neither provider owns the lesson loop.

Illustrative application contract, not an SDK signature:

```typescript
type VoiceSelection =
  | { kind: "preset"; speaker: string }
  | { kind: "custom"; profileId: string };

type SpeechRequest = {
  sessionId: string;
  lessonStepId: string;
  responseVersion: number;
  text: string;
  languageCode: string;
  voice: VoiceSelection;
};

type SpeechResult = {
  responseVersion: number;
  audioUrl: string; // application-served, short-lived; no API keys
  mimeType: string;
  actualVoice: VoiceSelection;
};

// Shared behavior: synthesize(request) -> SpeechResult or a typed error.
// Browser playback must stop locally even if provider cancellation is unavailable.
```

For the first version use complete short audio responses. Streaming can be added without changing the voice selection shape. Keep source text and speech chunks associated with their response version. Custom voice selection applies to subsequent synthesis requests; it must not reset the lesson.

## Proposed application routes

These are our future backend routes, **not Sarvam's endpoints**:

| Route | Owner | Purpose |
|---|---|---|
| `POST /api/voices` | Teammate | Receive reference audio and explicit rights confirmation; create a profile |
| `GET /api/voices` | Teammate | Return selectable application profiles |
| `POST /api/speech` | Shared; coordinate changes | Dispatch synthesis through the selected adapter |

Application profile shape: `id`, `displayName`, `kind`, `status` (`ready` or `failed`), optional provider voice identifier stored server-side, supported language metadata if verified, and consent metadata. Do not make up verified language coverage. A request-in-progress UI state is acceptable, but do not assume Sarvam voice creation returns a polling job.

The main builder may use different routes if already scaffolded; record the final interface here before integration. In a shared deployment, profile lists and media access must be scoped to the owning user/session. A local demo may use a single-session store, documented as such.

## Actual Sarvam custom-voice APIs

The current [create-voice reference](https://docs.sarvam.ai/api-reference/voice-cloning/create-voice) documents `POST /voices/create`, multipart audio, `name` and reference `language`; the response contains `data.voice_id`. Creation returns a usable saved voice inline. Do not model it as the asynchronous Document AI job flow.

The [speech-generation reference](https://docs.sarvam.ai/api-reference/voice-cloning/clone) documents `POST /voices/clone`: send text and exactly one of saved `voice_id` or inline `ref_audio`. Prefer a saved voice for repeated lessons. The adapter decodes the returned audio into the shared application speech result. It must respect text-size limits and short chunk ordering.

See the [overview](https://docs.sarvam.ai/api/api-guides-tutorials/voice-cloning/overview) for current SDK requirements and limits. Reference uploads and inline reference generation have different limits. Recheck documentation and actual account access during implementation; the feature is beta.

Explicit rights confirmation is an application requirement grounded in Sarvam's [voice-use requirements](https://docs.sarvam.ai/api/getting-started/commercial-licensing). Do not put a fictional `consent` field in a Sarvam request. Keep the confirmation in application metadata.

## Failure behavior

- Incomplete custom-voice work never blocks preset speech.
- Failed custom creation leaves the preset selection usable and explains the failure.
- Failed custom synthesis offers an explicitly labeled switch to the preset voice. Do not silently mislabel fallback audio.
- Stop/pause cancels browser playback and rejects late audio by response version.
- Keys and reference recordings remain on the backend. Runtime files stay outside Git.
- Changing voice affects presentation only; learner answers and lesson progress remain intact.
