"""Mocked browser state checks; no provider APIs or credits are used.

Run a Vite frontend, then: python tests/browser_flow.py
This verifies lesson controls, not actual audio output or microphone quality.
"""

from __future__ import annotations

import json
import os
import time

from playwright.sync_api import sync_playwright, expect


BASE = os.getenv("PAATH_TEST_URL", "http://127.0.0.1:5173")


def main():
    speech_texts = []
    counts = {"speech": 0, "answers": 0}
    step = {
        "id": "compare", "title": "Compare equal parts", "narration": "Original lesson explanation.",
        "board": {"heading": "Same whole", "bullets": ["Keep the wholes equal"], "fractionBars": [
            {"label": "One third", "parts": 3, "filled": 1},
            {"label": "One fourth", "parts": 4, "filled": 1},
        ]},
        "question": "Which is larger: 1/3 or 1/4? Explain why.",
        "expectedAnswer": "One third", "sourcePages": [],
    }
    lesson = {"id": "mock-lesson", "title": "Fractions demo", "language": "en-IN", "provider": "demo", "steps": [step]}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.add_init_script("""
          window.__audioPlays = 0;
          window.Audio = class {
            constructor(src) { this.src = src; this.onended = null; this.onerror = null; }
            async play() { window.__audioPlays++; this.timer = setTimeout(() => this.onended?.(), 40); }
            pause() { clearTimeout(this.timer); }
          };
        """)

        def api(route):
            request = route.request
            path = request.url.split("/api/", 1)[1]
            body = request.post_data_json if request.headers.get("content-type", "").startswith("application/json") else {}
            if path == "health":
                result = {"geminiConfigured": False, "sarvamConfigured": True, "model": "test-model"}
            elif path == "material":
                result = {"sourceId": "sample", "title": "Sample", "text": "Reviewed sample", "pages": [{"page": 1, "text": "Reviewed sample"}]}
            elif path == "lesson":
                assert body["mode"] == "demo"
                result = lesson
            elif path == "speech":
                counts["speech"] += 1
                speech_texts.append(body["text"])
                result = {"responseVersion": body["responseVersion"], "audioUrl": "/mock-audio", "mimeType": "audio/wav"}
            elif path == "answer":
                counts["answers"] += 1
                if counts["answers"] == 1:
                    result = {"status": "needs_work", "feedback": "Compare piece sizes.", "narration": "Repair explanation.", "followUpQuestion": "Now compare 1/2 and 1/5. Explain why."}
                else:
                    result = {"status": "correct", "feedback": "You compared equal wholes.", "narration": "Your reasoning connects."}
            elif path == "doubt":
                result = {"answer": "Doubt answer is separate.", "narration": "Doubt answer is separate."}
            else:
                route.fulfill(status=404, content_type="application/json", body=json.dumps({"detail": "Unexpected mocked route"}))
                return
            route.fulfill(content_type="application/json", body=json.dumps(result))

        page.route("**/api/**", api)
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Gemini key needed for your own material")).to_be_visible()
        page.get_by_role("button", name="Try the English fractions sample").click()
        expect(page.get_by_text("Prepared sample", exact=True).first).to_be_visible()
        page.get_by_role("button", name="Start teaching", exact=True).click()
        expect(page.get_by_role("heading", name="Your turn to think")).to_be_visible()
        before = counts["speech"]
        page.wait_for_timeout(200)
        assert counts["speech"] == before, "Teacher must wait at the learner checkpoint"
        assert not page.get_by_role("button", name="Finish this lesson").count()

        page.get_by_role("textbox", name="Your answer, in your words").fill("One fourth because four is bigger.")
        page.get_by_role("button", name="Share my thinking").click()
        expect(page.get_by_role("heading", name="Now compare 1/2 and 1/5. Explain why.")).to_be_visible()
        expect(page.get_by_role("heading", name="Your turn to think")).to_be_visible()
        assert not page.get_by_role("button", name="Finish this lesson").count()

        page.get_by_role("button", name="I have a doubt").click()
        page.get_by_role("textbox", name="What would you like to ask?").fill("Why keep the whole equal?")
        page.get_by_role("button", name="Ask my teacher").click()
        expect(page.get_by_role("heading", name="Lesson paused")).to_be_visible()
        assert speech_texts[-1] == "Doubt answer is separate."
        page.get_by_role("button", name="Resume teaching", exact=True).click()
        expect(page.get_by_role("heading", name="Your turn to think")).to_be_visible()
        assert speech_texts[-1] != "Doubt answer is separate.", "Resume repeated the doubt answer instead of teaching"

        page.get_by_role("textbox", name="Your answer, in your words").fill("One half is larger because fewer equal pieces make larger pieces.")
        page.get_by_role("button", name="Share my thinking").click()
        expect(page.get_by_role("button", name="Finish this lesson")).to_be_visible()
        page.get_by_role("button", name="Finish this lesson").click()
        expect(page.get_by_role("heading", name="You’ve reached the end of this lesson.")).to_be_visible()

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(100)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile page overflows horizontally"
        browser.close()
    print("Mocked browser checks passed: explicit demo, checkpoint wait, adaptive question, doubt/resume, completion and mobile overflow. No paid requests.")


if __name__ == "__main__":
    main()
