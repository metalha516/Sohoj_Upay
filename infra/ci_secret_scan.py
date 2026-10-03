"""Local secret scanner to verify zero secrets before commit, mirroring Gitleaks."""

import re
import sys
from pathlib import Path

RULES = [
    (
        "AWS Access Key",
        re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    ),
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub Token", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}")),
    (
        "Generic High-Entropy Secret",
        re.compile(
            r'(?i)(?:api_key|secret_key|private_key)\s*[:=]\s*["\'][A-Za-z0-9/\+=]{32,}["\']'
        ),
    ),
    (
        "Database URL with real password",
        re.compile(r"postgresql(?:\+asyncpg)?://(?!.*(?:\$\{|replace_with_))[^:]+:[^@]+@[^/]+"),
    ),
]

IGNORED_PATHS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def scan() -> int:
    root = Path(".")
    violations = []

    for file_path in root.rglob("*"):
        if file_path.is_dir() or any(p in file_path.parts for p in IGNORED_PATHS):
            continue

        if file_path.name in (".env.example", "test_logging.py", "logging.py", "ci_secret_scan.py"):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for rule_name, pattern in RULES:
            matches = pattern.findall(content)
            if matches:
                violations.append((file_path, rule_name, matches[:2]))

    if violations:
        print("[!] Secret Scan FAILED! Secrets found:")
        for path, rule, samples in violations:
            print(f"  - {path}: {rule} (matches: {samples})")
        return 1

    print("[PASS] Secret Scan PASSED! No secrets or credentials found.")
    return 0


if __name__ == "__main__":
    sys.exit(scan())
