"""Local Paath source intake service. Teaching controller is not implemented yet."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import json
import re

ROOT = Path(__file__).resolve().parent
STORE = ROOT / 'storage'
STORE.mkdir(exist_ok=True)
UPSTREAM = 'http://127.0.0.1:8765'

def fetch(path):
    with urlopen(UPSTREAM + path, timeout=10) as response:
        return response.read()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            data = (ROOT / 'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == '/api/recordings':
            try:
                self.reply([j for j in json.loads(fetch('/api/jobs')) if j['complete']])
            except (URLError, TimeoutError):
                self.reply({'error': 'Lecture Studio is unavailable. Start service 1.'}, 503)
        elif self.path == '/api/sources':
            self.reply([json.loads(p.read_text()) for p in STORE.glob('*.json')])
        else:
            self.reply({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:8766', 'http://localhost:8766'):
            return self.reply({'error': 'Invalid origin'}, 403)
        match = re.fullmatch(r'/api/import/([a-f0-9]{32})/([a-z]{2}-IN)', self.path)
        if not match:
            return self.reply({'error': 'Invalid import route'}, 400)
        job, language = match.groups()
        destination = STORE / f'{job}-{language}.json'
        if destination.exists():
            return self.reply(json.loads(destination.read_text()))
        try:
            jobs = json.loads(fetch('/api/jobs'))
            selected = next((j for j in jobs if j['id'] == job and j['complete'] and language in j['languages']), None)
            if selected is None:
                return self.reply({'error': 'Completed recording/language not found'}, 404)
            source = {'id': f'{job}-{language}', 'title': selected['name'], 'language': language,
                      'status': 'needs_review', 'origin': {'service': 'lecture-studio', 'job_id': job},
                      'notes': fetch(f'/jobs/{job}/{language}/notes.md').decode(),
                      'transcript': json.loads(fetch(f'/jobs/{job}/transcript.json')),
                      'slides': json.loads(fetch(f'/jobs/{job}/{language}/slides.json'))}
            temporary = destination.with_suffix('.tmp')
            temporary.write_text(json.dumps(source, ensure_ascii=False), encoding='utf-8')
            temporary.replace(destination)
            self.reply(source, 201)
        except (URLError, TimeoutError, ValueError):
            self.reply({'error': 'Could not import source. Check Lecture Studio outputs.'}, 502)

if __name__ == '__main__':
    print('Paath Live: http://127.0.0.1:8766', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
