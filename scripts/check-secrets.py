"""Check tracked and nonignored source files without displaying secret values.

Run before commits: python scripts/check-secrets.py
Ignored runtime data and local environment files are never read.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATTERNS = (
    ("Sarvam/API token", re.compile(r"\bsk_[A-Za-z0-9_-]{20,}\b")),
    ("Google API token", re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)
TEXT_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".md", ".txt", ".html", ".css", ".sh", ".ps1", ".example",
}


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return bool(re.fullmatch(r"sk_x+", lowered)) or lowered in {
        "your_api_key", "your_sarvam_api_key", "your_gemini_api_key",
    }


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return only line numbers and token categories, never token content."""
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in TOKEN_PATTERNS:
            if any(not is_placeholder(match.group()) for match in pattern.finditer(line)):
                findings.append((line_number, label))
    return findings


def git_paths(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", *args], cwd=ROOT,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout.decode("utf-8").rstrip("\0").split("\0") if result.stdout else []


def main() -> int:
    try:
        tracked = set(git_paths("--cached"))
        paths = tracked | set(git_paths("--others", "--exclude-standard"))
    except subprocess.CalledProcessError:
        print("Cannot inspect repository files. Run from a Git checkout.")
        return 2

    findings: list[str] = []
    for name in sorted(paths):
        path = Path(name)
        if name in tracked and path.name.startswith(".env") and path.name != ".env.example":
            findings.append(f"{name}: environment file is tracked")
            continue
        if path.suffix.lower() in {".pem", ".key"}:
            findings.append(f"{name}: possible private key file")
            continue
        full_path = ROOT / path
        if not full_path.is_file() or full_path.stat().st_size > 2_000_000:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".gitignore", ".env.example"}:
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(f"{name}:{line}: possible {label}" for line, label in scan_text(content))
        # The index can differ from the working tree: inspect the actual staged
        # bytes too, so deleting a leaked token locally cannot hide a staged copy.
        if name in tracked:
            staged = subprocess.run(
                ["git", "show", f":{name}"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if staged.returncode == 0 and len(staged.stdout) <= 2_000_000:
                try:
                    staged_content = staged.stdout.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if staged_content != content:
                    findings.extend(f"{name}:{line}: staged possible {label}" for line, label in scan_text(staged_content))

    if findings:
        print("Credential hygiene check failed (values redacted):")
        print("\n".join(findings))
        return 1
    print(f"Credential hygiene check passed: {len(paths)} tracked/nonignored files and their staged copies inspected; ignored environment files were not read.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
