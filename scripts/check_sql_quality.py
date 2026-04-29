import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DBT_MODELS = REPO_ROOT / "dbt_project" / "models"
ENFORCED_LAYER_DIRS = {"2_base", "3_core", "4_intermediate", "5_marts"}


def _is_enforced_sql(path: Path) -> bool:
    if path.suffix.lower() != ".sql":
        return False
    try:
        rel = path.resolve().relative_to(DBT_MODELS.resolve())
    except ValueError:
        return False
    parts = rel.parts
    return bool(parts and parts[0] in ENFORCED_LAYER_DIRS)


def _collect_target_files(argv: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in argv:
        p = Path(raw)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if not p.exists() or not p.is_file():
            continue
        if _is_enforced_sql(p):
            out.append(p)
    return sorted(set(out))


def _has_allow_comment(content: str) -> bool:
    return "sql-quality: allow-select-star" in content.lower()


def _check_file(path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(REPO_ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()

    if not _has_allow_comment(text):
        if re.search(r"\bselect\s+\*", lowered):
            errors.append(
                f"{rel}: avoid `select *` in base/core/intermediate/marts (project SQL quality gate)."
            )

    has_rank_alias = bool(re.search(r"\brow_number\s*\(\)\s*over\b", lowered))
    has_where_rn = bool(re.search(r"\bwhere\s+rn\s*=\s*1\b", lowered))
    has_qualify = "qualify" in lowered
    if has_rank_alias and has_where_rn and not has_qualify:
        errors.append(
            f"{rel}: prefer `qualify row_number() ... = 1` over `where rn = 1` for simple dedupe."
        )

    return errors


def main() -> int:
    files = _collect_target_files(sys.argv[1:])
    if not files:
        print("SQL quality gate: no changed enforced-layer SQL files found.")
        return 0

    errors: list[str] = []
    for f in files:
        errors.extend(_check_file(f))

    if errors:
        print("SQL quality gate failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"SQL quality gate passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
