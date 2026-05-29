from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from displaycal_inventory import inventory_path
from displaycal_correction_parser import extract_correction_metadata
from displaycal_profile_parser import extract_icc_metadata
from displaycal_report_parser import extract_report_fields


def extract_file(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return {
            "artifact_role": "report_html",
            "report_fields": extract_report_fields(path.read_text(encoding="utf-8", errors="replace")),
        }
    if suffix in {".icc", ".icm"}:
        return {"artifact_role": "icc_profile", "profile_fields": extract_icc_metadata(path)}
    if suffix in {".ccss", ".ccmx"}:
        return {
            "artifact_role": "spectral_correction" if suffix == ".ccss" else "matrix_correction",
            "correction_fields": extract_correction_metadata(path),
        }
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for item in inventory_path(args.root):
        path = Path(str(item["path"]))
        enriched = item | extract_file(path)
        records.append(enriched)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
