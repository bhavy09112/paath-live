# Build notes

## Provider decision

The user explicitly changed the teaching model from Sarvam 105B to **Gemini Flash**. Sarvam remains the speech provider. The Flash model identifier is configurable. No live Gemini request has been tested without its key.

## Sarvam smoke test

One short speech request and one transcription request were made using the local Sarvam key. Both returned HTTP 200, with no retries. The synthesized phrase was “Welcome to Paath Live.” The transcript was “Welcome to Path Life,” showing that brand-name recognition is imperfect. Students should review transcripts before submitting them for assessment.

Exact billed credits were not measured. Test media lives in ignored local storage and is not committed. Automated checks must mock external providers.

## Limits

- Sample lessons are scripted fixtures, explicitly labeled.
- Live lessons, feedback and doubts require Gemini credentials and live validation.
- Source extraction handles text PDFs; scans need pasted text in this version.
- This is a local single-user app with in-memory sessions, not a public multi-user service.
- Custom voice uploads are the teammate's feature; the core implements preset speech only.
- Turn control uses explicit pause/ask rather than automatic spoken barge-in.

## Teammate seam

Use `POST /api/speech` as the synthesis boundary with response-version correlation. Custom selections are modeled but intentionally unimplemented. Saved-voice creation, preview and selection belong in the teammate's branch. Update `docs/ARCHITECTURE.md` if a shared route changes.
