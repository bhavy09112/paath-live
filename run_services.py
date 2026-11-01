"""Run both local services. Ctrl+C stops both."""
from pathlib import Path
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parent
children = []
try:
    for name in ('lecture-studio', 'paath-live'):
        children.append(subprocess.Popen([sys.executable, str(ROOT / 'services' / name / 'server.py')]))
    while all(p.poll() is None for p in children):
        time.sleep(.5)
finally:
    for p in children:
        if p.poll() is None:
            p.terminate()
    for p in children:
        p.wait()
