from __future__ import annotations

from pathlib import Path
import re


HEADER_PATTERN = re.compile(r'^\s*([A-Z0-9_]+)\s+"?([^"\r\n]*)"?\s*$')


def extract_correction_metadata(path: Path) -> dict[str, object]:
    metadata: dict[str, object] = {
        "path": str(path),
        "filename": path.name,
        "correction_type": path.suffix.lower().lstrip("."),
    }
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped in {"BEGIN_DATA_FORMAT", "BEGIN_DATA"}:
            break
        match = HEADER_PATTERN.match(stripped)
        if not match:
            continue
        key, value = match.groups()
        metadata[key.casefold().lower()] = value.strip()
    return metadata
