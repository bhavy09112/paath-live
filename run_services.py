"""Run both local services. Ctrl+C stops both."""
from pathlib import Path
import os
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parent
children = []
os.environ.setdefault('LECTURE_ENV_FILE', str(ROOT / '.env'))
if not (ROOT / 'frontend/node_modules/vite/bin/vite.js').exists():
    raise SystemExit('Run npm --prefix frontend ci first.')
try:
    for name in ('lecture-studio', 'paath-live'):
        children.append(subprocess.Popen([sys.executable, str(ROOT / 'services' / name / 'server.py')]))
    children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'], cwd=ROOT))
    children.append(subprocess.Popen(['node', str(ROOT / 'frontend/node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '5173', '--strictPort'], cwd=ROOT / 'frontend'))
    print('Interactive teacher: http://127.0.0.1:5173', flush=True)
    while all(p.poll() is None for p in children):
        time.sleep(.5)
finally:
    for p in children:
        if p.poll() is None:
            p.terminate()
    for p in children:
        p.wait()
