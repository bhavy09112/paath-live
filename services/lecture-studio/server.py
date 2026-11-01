from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse, parse_qs
import uuid
from pipeline import DATA, ROOT, LANGUAGES, run, save

DATA.mkdir(exist_ok=True)
pool = ThreadPoolExecutor(max_workers=1)
active = {}

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/jobs':
            return self.reply([json.loads(p.read_text()) for p in sorted(DATA.glob('*/status.json'), reverse=True)])
        if path == '/':
            file = ROOT / 'index.html'
        elif re.fullmatch(r'/jobs/[a-f0-9]{32}/[\w./-]+', path):
            file = (DATA / path.removeprefix('/jobs/')).resolve()
            if DATA not in file.parents or file.suffix not in {'.md', '.json', '.html', '.wav'} or 'chunks' in file.parts:
                return self.reply({'error': 'Not found'}, 404)
        else:
            return self.reply({'error': 'Not found'}, 404)
        if not file.is_file():
            return self.reply({'error': 'Not found'}, 404)
        self.send_response(200)
        self.send_header('Content-Type', self.guess_type(str(file)))
        self.send_header('Content-Length', str(file.stat().st_size))
        self.end_headers()
        with file.open('rb') as stream:
            shutil.copyfileobj(stream, self.wfile)

    def do_POST(self):
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:8765', 'http://localhost:8765'):
            return self.reply({'error': 'Invalid origin'}, 403)
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/retry/'):
            job = parsed.path.rsplit('/', 1)[-1]
            if not re.fullmatch('[a-f0-9]{32}', job) or not (DATA / job / 'status.json').exists():
                return self.reply({'error': 'Unknown job'}, 404)
            if job not in active or active[job].done():
                active[job] = pool.submit(run, job)
            return self.reply({'id': job})
        if parsed.path != '/api/upload':
            return self.reply({'error': 'Not found'}, 404)
        query = parse_qs(parsed.query)
        languages = query.get('languages', ['en-IN,hi-IN'])[0].split(',')
        try:
            length = int(self.headers.get('Content-Length', 0))
        except ValueError:
            length = 0
        if not 0 < length <= 500 * 1024 * 1024 or not languages or any(x not in LANGUAGES for x in languages):
            return self.reply({'error': 'Choose supported languages and a file under 500 MB.'}, 400)
        try:
            start = float(query.get('start', ['0'])[0])
            duration = float(query.get('duration', ['0'])[0])
            if not (0 <= start <= 86400 and 0 <= duration <= 86400):
                raise ValueError()
        except ValueError:
            return self.reply({'error': 'Enter valid start and duration values.'}, 400)
        job = uuid.uuid4().hex
        folder = DATA / job
        folder.mkdir()
        remaining = length
        with (folder / 'input.mp3').open('wb') as output:
            while remaining:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    shutil.rmtree(folder)
                    return
                output.write(chunk)
                remaining -= len(chunk)
        save(folder / 'status.json', {'id': job, 'name': query.get('name', ['Lecture'])[0][:180], 'languages': languages, 'sample': False, 'start_seconds': start, 'duration_seconds': duration, 'stage': 'Queued', 'complete': False})
        active[job] = pool.submit(run, job)
        self.reply({'id': job}, 202)

if __name__ == '__main__':
    print('Lecture Studio: http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
