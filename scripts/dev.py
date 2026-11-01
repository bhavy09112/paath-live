"""Run Paath Live's local API and frontend; credentials remain on the API."""
from pathlib import Path
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    processes = []
    try:
        processes.append(subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'],
            cwd=ROOT,
        ))
        command = ['node', str(ROOT / 'frontend' / 'node_modules' / 'vite' / 'bin' / 'vite.js'),
                   '--host', '127.0.0.1', '--port', '5173', '--strictPort']
        processes.append(subprocess.Popen(command, cwd=ROOT / 'frontend'))
        print('Paath Live: http://127.0.0.1:5173 (API: http://127.0.0.1:8000)', flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(0.4)
        return next((p.returncode for p in processes if p.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

if __name__ == '__main__':
    raise SystemExit(main())
