import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "docs" / "images" / "readme"
MAX_BYTES = 300 * 1024


def test_every_readme_image_exists_and_is_small():
    referenced = re.findall(r'src="(docs/images/readme/[^"]+\.png)"', (ROOT / "README.md").read_text(encoding="utf-8"))
    assert len(referenced) == 30
    for rel in referenced:
        path = ROOT / rel
        assert path.is_file(), rel
        assert path.stat().st_size <= MAX_BYTES, rel


def test_no_unreferenced_readme_image():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r'docs/images/readme/([^"]+\.png)', text))
    assert {p.name for p in IMAGES.glob("*.png")} == referenced
