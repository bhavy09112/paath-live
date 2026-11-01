# Short guide for the teammate's AI

Paste this into your AI after cloning this repository:

> Read `AGENTS.md`, `README.md` and `docs/ARCHITECTURE.md`. We are building **Paath Live**, a Sarvam-powered agent that proactively teaches supplied material, asks questions, adapts explanations and resumes after doubts. The repository initially contains documentation; inspect the current code before assuming modules or routes exist.
>
> **Your task is only the custom teacher-voice feature:** let the user upload an authorized voice reference recording, create a reusable voice profile, preview it and select it for the teacher's future speech. Do not build or rewrite the lesson controller, PDF processing, assessment or board.
>
> Integrate through the shared `VoiceSelection` and speech-provider boundary in `docs/ARCHITECTURE.md`. Standard Bulbul speech must work while your feature is incomplete. Coordinate the shared synthesis route/types with the main builder and preserve their edits. Keep lesson text, state and response-version cancellation unchanged.
>
> Prefer Sarvam's saved-voice path: create once, retain the returned voice ID server-side, then synthesize new lesson text using that ID. Confirm actual API fields, SDK version, audio limits and account support against the official links below. Collect explicit voice-rights confirmation before provider upload. Keep keys, reference recordings and generated media out of Git.
>
> Work on `feat/custom-teacher-voice`. Add the smallest upload/profile/preview UI and backend adapter consistent with the app's actual stack. Check upload rejection, preview playback, selection, provider failure, correctly labeled fallback, and interruption/stale-response behavior. Report precisely what is implemented, mocked and tested. Open a focused PR with run instructions and any shared interface changes.

References: [create voice](https://docs.sarvam.ai/api-reference/voice-cloning/create-voice), [generate speech](https://docs.sarvam.ai/api-reference/voice-cloning/clone), [overview and SDK requirements](https://docs.sarvam.ai/api/api-guides-tutorials/voice-cloning/overview).

This feature means generating new teaching speech in the supplied voice. Uploading a recorded lecture as lesson content is a different feature.
