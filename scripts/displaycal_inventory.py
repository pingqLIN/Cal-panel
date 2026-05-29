from __future__ import annotations

import argparse
import json
from pathlib import Path


ARTIFACT_EXTENSIONS = {
    ".7z": "archive",
    ".cal": "calibration_curves",
    ".ccmx": "matrix_correction",
    ".ccss": "spectral_correction",
    ".gz": "compressed_data",
    ".html": "report_html",
    ".icc": "icc_profile",
    ".icm": "icc_profile",
    ".log": "displaycal_log",
    ".png": "plot",
    ".ti1": "testchart",
    ".ti3": "measurements",
    ".wrz": "vrml_gamut",
    ".zip": "archive",
}


def classify(path: Path) -> str:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes[-2:] == [".gam", ".gz"]:
        return "gamut_data"
    return ARTIFACT_EXTENSIONS.get(path.suffix.lower(), "other")


def inventory_path(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        records.append(
            {
                "source_kind": "local",
                "path": str(path),
                "folder": str(path.parent),
                "filename": path.name,
                "extension": "".join(path.suffixes),
                "artifact_role": classify(path),
                "size_bytes": stat.st_size,
                "modified_time_epoch": stat.st_mtime,
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = inventory_path(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
