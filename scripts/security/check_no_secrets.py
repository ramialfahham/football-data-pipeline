import pathlib
import re
import sys


SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"(?i)aws(.{0,20})?(secret|access).{0,20}[=:].{0,10}[A-Za-z0-9/+=]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"(?i)xox[baprs]-[A-Za-z0-9-]{10,}"),  # Slack tokens
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),  # GitHub personal access tokens
)

SAFE_HINTS = ("replace_with_", "example", "placeholder", "dummy", "sample")
TEXT_EXTENSIONS = {
    ".py",
    ".sql",
    ".yml",
    ".yaml",
    ".md",
    ".mdc",
    ".json",
    ".txt",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".env",
    ".cfg",
    ".ini",
    ".gs",
}


def should_scan(path: pathlib.Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS and path.is_file()


def looks_safe(line: str) -> bool:
    lowered = line.lower()
    return any(h in lowered for h in SAFE_HINTS)


def main() -> int:
    files = [pathlib.Path(p) for p in sys.argv[1:]]
    findings: list[str] = []

    for file_path in files:
        if not should_scan(file_path):
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for idx, line in enumerate(content.splitlines(), start=1):
            if looks_safe(line):
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{file_path}:{idx}: potential secret matched `{pattern.pattern}`")
                    break

    if findings:
        print("Secret scan failed. Remove or replace sensitive values before commit.")
        for finding in findings:
            print(f" - {finding}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
