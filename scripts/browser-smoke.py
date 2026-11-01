"""Real browser + local backend check. Speech is mocked: no paid provider calls.

Run against npm run dev with Playwright/Chromium installed.
"""
from pathlib import Path
import base64
import io
import json
import re
import wave
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'artifacts'
out.mkdir(exist_ok=True)
buffer = io.BytesIO()
with wave.open(buffer, 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(16000)
    wav.writeframes(b'\x00\x00' * 3200)
mock_url = 'data:audio/wav;base64,' + base64.b64encode(buffer.getvalue()).decode()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1050})
    page.set_default_timeout(10000)
    errors = []
    calls = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def speech(route):
        payload = route.request.post_data_json
        calls.append(payload['text'])
        route.fulfill(status=200, content_type='application/json', body=json.dumps({
            'responseVersion': payload['responseVersion'], 'audioUrl': mock_url,
            'mimeType': 'audio/wav', 'actualVoice': {'kind': 'preset', 'speaker': 'mock'},
        }))

    page.route('**/api/speech', speech)
    page.route('**/api/transcribe', lambda route: route.fulfill(
        status=200, content_type='application/json',
        body=json.dumps({'transcript': 'Four equal parts make the whole.', 'languageCode': 'en-IN'})))
    page.goto('http://127.0.0.1:5173')
    page.wait_for_load_state('networkidle')
    expect(page.get_by_role('heading', name='Prepare your lesson')).to_be_visible()
    page.screenshot(path=str(out / 'setup-desktop.png'), full_page=True)
    page.get_by_role('button', name=re.compile('Try the .*fractions sample')).click()
    expect(page.get_by_text('Prepared sample', exact=True).first).to_be_visible()
    page.get_by_role('button', name='Start teaching', exact=True).click()
    expect(page.get_by_role('heading', name='Your turn to think', exact=True)).to_be_visible(timeout=10000)
    page.get_by_label('Your answer, in your words').fill('Four equal parts make the whole.')
    page.get_by_role('button', name='Share my thinking').click()
    expect(page.get_by_text('That reasoning connects.', exact=True)).to_be_visible()
    page.get_by_role('button', name='Continue to the next concept').click()
    expect(page.get_by_role('heading', name='Your turn to think', exact=True)).to_be_visible(timeout=10000)
    page.get_by_label('Your answer, in your words').fill('1/4 is larger than 1/3 because four is bigger.')
    page.get_by_role('button', name='Share my thinking').click()
    expect(page.get_by_text('Let’s try another way.', exact=True)).to_be_visible()
    expect(page.get_by_role('heading', name='Return to the same whole')).to_be_visible()
    page.screenshot(path=str(out / 'lesson-repair-desktop.png'), full_page=True)
    page.get_by_role('button', name='I have a doubt').click()
    page.get_by_label('What would you like to ask?').fill('Why must the whole be the same size?')
    page.get_by_role('button', name='Ask my teacher').click()
    expect(page.get_by_role('heading', name='Lesson paused', exact=True)).to_be_visible(timeout=10000)
    page.get_by_role('button', name='Resume teaching', exact=True).click()
    expect(page.get_by_role('heading', name='Your turn to think', exact=True)).to_be_visible(timeout=10000)
    assert 'In this reviewed fractions demo' not in calls[-1], 'Resume replayed doubt instead of lesson position'
    page.get_by_label('Your answer, in your words').fill('One half is larger because the same whole has fewer equal pieces.')
    page.get_by_role('button', name='Share my thinking').click()
    expect(page.get_by_text('That reasoning connects.', exact=True)).to_be_visible()
    page.set_viewport_size({'width': 390, 'height': 844})
    page.screenshot(path=str(out / 'lesson-mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
    assert not errors, errors
    print('Browser smoke passed: sample, teaching, correct reasoning, misconception repair, doubt/resume, mobile layout.')
    print('Speech requests mocked:', len(calls), '; paid browser-test provider calls: 0')
    browser.close()
