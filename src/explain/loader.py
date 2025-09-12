# src/explain/loader.py
import json
import pathlib
from typing import Dict

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (…/aksmigrate)
RULES_DIR = ROOT / "rules"
INDEX_FILE = RULES_DIR / "index.json"


def load_explanation(rule_id: str) -> Dict[str, str]:
    """
    Returns { 'why': str, 'source': str } for the given rule_id.
    Looks up rules/index.json -> markdown file -> reads 'Why:' and 'Source:' lines.
    Fallbacks to empty strings if not found.
    """
    try:
        idx = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        md_name = idx.get(rule_id)
        if not md_name:
            return {"why": "", "source": ""}

        md_path = RULES_DIR / md_name
        if not md_path.exists():
            return {"why": "", "source": ""}

        why, src = "", ""
        for line in md_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.lower().startswith("why:"):
                why = line.split(":", 1)[1].strip()
            elif line.lower().startswith("source:"):
                src = line.split(":", 1)[1].strip()
        return {"why": why, "source": src}
    except Exception:
        return {"why": "", "source": ""}
