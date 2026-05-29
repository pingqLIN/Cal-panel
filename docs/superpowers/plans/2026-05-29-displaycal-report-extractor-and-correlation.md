# DisplayCAL Report Extractor and Correlation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable research and extraction workflow for DisplayCAL-generated ICC/ICM packages and verification reports from Google Drive `我的雲端硬碟/00-custom` plus local DisplayCAL storage.

**Architecture:** Keep the workflow local-first: inventory inputs, preserve source paths/Drive IDs, extract report/profile metadata into structured JSON/CSV, then derive monitor/hardware/calibration correlations from that normalized dataset. Use small Python modules so HTML report parsing, ICC/ICM inspection, archive inventory, and correlation analysis can be tested independently.

**Tech Stack:** Python standard library, BeautifulSoup if already available or `html.parser` fallback, optional Pillow/ImageCms for ICC header/tag reads, PowerShell for Windows path inventory, Google Drive connector for Drive grounding.

---

## Working Assumptions

- Workspace root: `Q:\Projects\Cal-panel`.
- This folder is currently not a Git repository, so no branch/commit steps are included unless the project is initialized later.
- Primary Drive folder: `https://drive.google.com/drive/folders/1Yvi9zvdut7oODAjk-QGinyIEXukU3Xp6` (`00-custom`).
- First grounded Drive sample: `20230825 林嘉萱`, folder ID `1QryRRmdSLGOrGjqmenS_zBd7kGji2H28`.
- Local sample folder: `C:\Users\miles\AppData\Roaming\DisplayCAL\storage\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX`.
- Preserve raw artifacts in place. Generated research files go under `research/displaycal/`; extraction tools go under `scripts/`.

## File Structure

- Create: `scripts/displaycal_extract.py`
  - CLI entrypoint. Accepts local files/folders, optional manifest JSON, and emits normalized JSON/CSV.
- Create: `scripts/displaycal_report_parser.py`
  - Parses DisplayCAL HTML verification/report files, especially self-contained hidden inputs such as `FF_display`, `FF_instrument`, `FF_correction_matrix`, `FF_profile`, `FF_data_in`, and `FF_data_ref`.
- Create: `scripts/displaycal_profile_parser.py`
  - Reads ICC/ICM profile metadata using safe local libraries or a minimal binary fallback.
- Create: `scripts/displaycal_inventory.py`
  - Builds local inventory from folders, archives, and report/profile sidecars.
- Create: `scripts/displaycal_correlate.py`
  - Groups cases by display model, target white point/gamma, instrument, correction file, profile type, and report outcomes.
- Create: `tests/test_displaycal_report_parser.py`
  - Locks parser behavior against small HTML fixtures derived from actual DisplayCAL report structure.
- Create: `tests/test_displaycal_profile_parser.py`
  - Locks ICC/ICM metadata extraction using a tiny fixture or skipped integration path if binary fixture is unavailable.
- Create: `research/displaycal/drive_inventory.json`
  - Drive-grounded file/folder list with IDs, titles, MIME types, modified times, and source folder path.
- Create: `research/displaycal/local_inventory.json`
  - Local DisplayCAL storage inventory with filenames, sizes, modified times, extensions, and inferred artifact roles.
- Create: `research/displaycal/extracted_records.json`
  - Normalized extraction output from sampled Drive/local artifacts.
- Create: `research/displaycal/correlation_report.md`
  - Human-readable analysis of report format, key fields, display model/spec relationships, and correction-file usage.

## Key Fields To Extract

- Source identity: source kind, Drive ID or local absolute path, source folder, filename, modified time, size.
- Display identity: display name/model from filename, report title, profile description, EDID/manufacturer fields if present.
- Calibration target: white point xy/CCT, tone curve/gamma, luminance target, black point, profile type, calibration speed/quality when present.
- Measurement device: instrument name, display type mode, observer, measurement mode, calibration speed, ambient/flare settings when present.
- Correction data: `.ccss` or `.ccmx` file name, correction description, display technology/backlight hints, spectral sample count if available.
- Report metrics: average/max delta E, white point error, gamma/TRC behavior, contrast, black/white luminance, RGB balance summary, pass/fail style status when present.
- Embedded report payloads: `FF_*` hidden inputs and embedded CGATS/CTI3 data blocks from `FF_data_in` and `FF_data_ref`.
- Artifact relationships: CAL/UNCAL pair, ICC/ICM profile, `.ti1`, `.ti3`, `.cal`, `.gam.gz`, `.wrz`, archive members, screenshots/CLUT plots.

## Task 1: Ground And Inventory Inputs

**Files:**
- Create: `research/displaycal/drive_inventory.json`
- Create: `research/displaycal/local_inventory.json`
- Create: `scripts/displaycal_inventory.py`

- [ ] **Step 1: Capture Drive sample inventory**

Use Google Drive folder listing for `00-custom`, then recurse only into candidate calibration folders. Start with:

```text
00-custom/20230825 林嘉萱
```

Expected candidate artifacts:

```text
ColorGeek_CAL_VZ249HEG1R @ 0, 0, 1920x1080 — 2023-08-25 15-33.html
ColorGeek_UNCAL_VZ249HEG1R @ 0, 0, 1920x1080 — 2023-08-25 15-33.html
ColorGeek_ASUS VZ249HEG1R 2023-08-25 16-32 0.3132x 0.3326y 2.2 F-S XYZLUT+MTX.7z
ColorGeek_CAL_SA241Y H @ 0, 0, 1920x1080 — 2023-08-25 15-59.html
ColorGeek_UNCAL_SA241Y H @ 0, 0, 1920x1080 — 2023-08-25 15-59.html
ColorGeek_ACER SA241Y H 2023-08-25 16-10 0.3127x 0.329y 2.2 F-S XYZLUT+MTX.zip
ColorGeek_CAL Built-in Retina Display @ 0, 0, 1280x800 — 2023-08-25 16-55.html
ColorGeek_UNCAL Built-in Retina Display @ 0, 0, 1280x800 — 2023-08-25 16-55.html
ColorGeek_Display #1 2023-08-25 17-23 0.3124x 0.3321y 2.2 F-S 1xCurve+MTX.zip
```

- [ ] **Step 2: Write local inventory script**

Implement `scripts/displaycal_inventory.py` with:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

ARTIFACT_EXTENSIONS = {
    ".html": "report_html",
    ".icc": "icc_profile",
    ".icm": "icc_profile",
    ".ccss": "spectral_correction",
    ".ccmx": "matrix_correction",
    ".cal": "calibration_curves",
    ".ti1": "testchart",
    ".ti3": "measurements",
    ".log": "displaycal_log",
    ".wrz": "vrml_gamut",
    ".zip": "archive",
    ".7z": "archive",
    ".gz": "compressed_data",
    ".png": "plot",
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
```

- [ ] **Step 3: Run local inventory**

Run:

```powershell
python scripts\displaycal_inventory.py "C:\Users\miles\AppData\Roaming\DisplayCAL\storage\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX" --out research\displaycal\local_inventory.json
```

Expected: `local_inventory.json` contains one record per DisplayCAL artifact, including `Dell_U2413_25Jul12.ccss` and the `.icm` profile.

## Task 2: Parse DisplayCAL HTML Reports

**Files:**
- Create: `scripts/displaycal_report_parser.py`
- Create: `tests/test_displaycal_report_parser.py`

- [ ] **Step 1: Write fixture-driven parser test**

Create `tests/test_displaycal_report_parser.py`:

```python
from scripts.displaycal_report_parser import extract_report_fields


def test_extracts_displaycal_report_key_value_pairs() -> None:
    html = """
    <html><head><title>ColorGeek_CAL_VZ249HEG1R @ 0, 0, 1920x1080</title></head>
      <body>
        <h2 id="reporttitle">VZ249HEG1R @ 0, 0, 1920x1080 — 2023-08-25 15:54:56</h2>
        <input type="hidden" name="FF_display" value="VZ249HEG1R @ 0, 0, 1920x1080" />
        <input type="hidden" name="FF_instrument" value="i1 DisplayPro, ColorMunki Display — LCD (generic)" />
        <input type="hidden" name="FF_correction_matrix" value="i1 DisplayPro, ColorMunki Display & ASUSTek COMPUTER INC VZ249HEG1R (i1 Pro 3).ccmx" />
        <input type="hidden" name="FF_profile" value="ColorGeek_ASUS VZ249HEG1R 2023-08-25 15-43 D6500 2.2 F-S XYZLUT+MTX" />
        <input type="hidden" name="FF_report_version" value="3.8.9.3" />
        <input type="hidden" name="FF_data_in" value="CTI3&#10;NUMBER_OF_FIELDS 4&#10;BEGIN_DATA_FORMAT&#10;SAMPLE_ID RGB_R RGB_G RGB_B&#10;END_DATA_FORMAT&#10;NUMBER_OF_SETS 1&#10;BEGIN_DATA&#10;1 100 100 100&#10;END_DATA" />
      </body>
    </html>
    """
    fields = extract_report_fields(html)
    assert fields["title"] == "Measurement Report 3.8.9.3 — VZ249HEG1R"
    assert fields["display"] == "VZ249HEG1R"
    assert fields["instrument"] == "i1 DisplayPro, ColorMunki Display — LCD (generic)"
    assert fields["correction_file"] == "i1 DisplayPro, ColorMunki Display & ASUSTek COMPUTER INC VZ249HEG1R (i1 Pro 3).ccmx"
    assert fields["correction_type"] == "ccmx"
    assert fields["profile"] == "ColorGeek_ASUS VZ249HEG1R 2023-08-25 15-43 D6500 2.2 F-S XYZLUT+MTX"
    assert fields["report_version"] == "3.8.9.3"
    assert fields["measurement_patch_count"] == "1"
```

- [ ] **Step 2: Implement HTML report parser**

Create `scripts/displaycal_report_parser.py`:

```python
from __future__ import annotations

from html.parser import HTMLParser
import re


FIELD_ALIASES = {
    "display": "display",
    "display device": "display",
    "instrument": "instrument",
    "measurement device": "instrument",
    "whitepoint": "whitepoint",
    "white point": "whitepoint",
    "tone curve": "tone_curve",
    "gamma": "gamma",
    "profile": "profile",
    "profile type": "profile_type",
    "average Δe*00": "average_de00",
    "average de00": "average_de00",
    "maximum Δe*00": "maximum_de00",
    "maximum de00": "maximum_de00",
    "contrast": "contrast",
    "white level": "white_luminance",
    "black level": "black_luminance",
}


class DisplaycalHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.current_tag: str | None = None
        self.hidden_inputs: dict[str, str] = {}
        self.in_report_title = False
        self.report_title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.current_tag = tag.lower()
        if self.current_tag == "title":
            self.in_title = True
        attrs_dict = {name.casefold(): value or "" for name, value in attrs}
        if self.current_tag == "h2" and attrs_dict.get("id") == "reporttitle":
            self.in_report_title = True
        if self.current_tag == "input" and attrs_dict.get("type", "").casefold() == "hidden":
            name = attrs_dict.get("name", "")
            if name.startswith("FF_"):
                self.hidden_inputs[name] = attrs_dict.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "h2":
            self.in_report_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_report_title:
            self.report_title_parts.append(data)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_key(value: str) -> str:
    key = normalize_text(value).casefold().rstrip(":")
    key = key.replace("delta e", "de").replace("∆", "Δ")
    return FIELD_ALIASES.get(key, re.sub(r"[^a-z0-9]+", "_", key).strip("_"))


def extract_report_fields(html: str) -> dict[str, str]:
    parser = DisplaycalHtmlParser()
    parser.feed(html)
    fields: dict[str, str] = {}
    title = normalize_text(" ".join(parser.title_parts))
    if title:
        fields["title"] = title
    report_title = normalize_text(" ".join(parser.report_title_parts))
    if report_title:
        fields["report_title"] = report_title
    for raw_key, value in parser.hidden_inputs.items():
        key = normalize_key(raw_key.removeprefix("FF_"))
        fields[key] = normalize_text(value)
    if "correction_matrix" in fields:
        fields["correction_file"] = fields["correction_matrix"]
        lowered = fields["correction_matrix"].casefold()
        fields["correction_type"] = "ccmx" if ".ccmx" in lowered else "ccss" if ".ccss" in lowered else "unknown"
    return fields
```

- [ ] **Step 3: Run parser test**

Run:

```powershell
python -m pytest tests\test_displaycal_report_parser.py -q
```

Expected: parser unit test passes before using real reports.

## Task 3: Parse ICC/ICM Profile Metadata

**Files:**
- Create: `scripts/displaycal_profile_parser.py`
- Create: `tests/test_displaycal_profile_parser.py`

- [ ] **Step 1: Implement binary-safe ICC description extraction**

Create `scripts/displaycal_profile_parser.py`:

```python
from __future__ import annotations

from pathlib import Path
import struct


def read_icc_tag_table(data: bytes) -> dict[str, tuple[int, int]]:
    if len(data) < 132:
        return {}
    tag_count = struct.unpack(">I", data[128:132])[0]
    tags: dict[str, tuple[int, int]] = {}
    offset = 132
    for _ in range(tag_count):
        if offset + 12 > len(data):
            break
        signature = data[offset : offset + 4].decode("latin1", errors="replace")
        tag_offset, tag_size = struct.unpack(">II", data[offset + 4 : offset + 12])
        tags[signature] = (tag_offset, tag_size)
        offset += 12
    return tags


def parse_text_tag(raw: bytes) -> str | None:
    if len(raw) < 8:
        return None
    tag_type = raw[:4].decode("latin1", errors="replace")
    if tag_type == "desc" and len(raw) >= 12:
        length = struct.unpack(">I", raw[8:12])[0]
        text = raw[12 : 12 + max(length - 1, 0)].decode("ascii", errors="replace")
        return text.strip("\x00").strip()
    if tag_type == "mluc" and len(raw) >= 16:
        count, record_size = struct.unpack(">II", raw[8:16])
        if count and record_size >= 12 and len(raw) >= 16 + record_size:
            length, offset = struct.unpack(">II", raw[20:28])
            text = raw[offset : offset + length].decode("utf-16-be", errors="replace")
            return text.strip("\x00").strip()
    if tag_type == "text":
        return raw[8:].decode("ascii", errors="replace").strip("\x00").strip()
    return None


def extract_icc_metadata(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    tags = read_icc_tag_table(data)
    metadata: dict[str, object] = {
        "path": str(path),
        "size_bytes": len(data),
        "preferred_cmm": data[4:8].decode("latin1", errors="replace") if len(data) >= 8 else "",
        "profile_version_major": data[8] if len(data) >= 9 else None,
        "device_class": data[12:16].decode("latin1", errors="replace") if len(data) >= 16 else "",
        "color_space": data[16:20].decode("latin1", errors="replace") if len(data) >= 20 else "",
        "pcs": data[20:24].decode("latin1", errors="replace") if len(data) >= 24 else "",
        "tag_signatures": sorted(tags),
    }
    for signature in ("desc", "dmnd", "dmdd", "cprt"):
        if signature not in tags:
            continue
        offset, size = tags[signature]
        if offset + size <= len(data):
            text = parse_text_tag(data[offset : offset + size])
            if text:
                metadata[signature] = text
    return metadata
```

- [ ] **Step 2: Add integration smoke test for the local `.icm` when present**

Create `tests/test_displaycal_profile_parser.py`:

```python
from pathlib import Path

from scripts.displaycal_profile_parser import extract_icc_metadata


LOCAL_PROFILE = Path(
    r"C:\Users\miles\AppData\Roaming\DisplayCAL\storage\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX"
    r"\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX.icm"
)


def test_extracts_local_icm_metadata_when_available() -> None:
    if not LOCAL_PROFILE.exists():
        return
    metadata = extract_icc_metadata(LOCAL_PROFILE)
    assert metadata["size_bytes"] > 128
    assert metadata["device_class"]
    assert "tag_signatures" in metadata
```

- [ ] **Step 3: Run profile parser test**

Run:

```powershell
python -m pytest tests\test_displaycal_profile_parser.py -q
```

Expected: pass, or no-op only if the local profile path is absent.

## Task 4: Build Unified Extraction CLI

**Files:**
- Create: `scripts/displaycal_extract.py`
- Create: `research/displaycal/extracted_records.json`

- [ ] **Step 1: Implement CLI orchestration**

Create `scripts/displaycal_extract.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from displaycal_inventory import inventory_path
from displaycal_profile_parser import extract_icc_metadata
from displaycal_report_parser import extract_report_fields


def extract_file(path: Path) -> dict[str, object]:
    record: dict[str, object] = {"path": str(path), "filename": path.name}
    suffix = path.suffix.lower()
    if suffix == ".html":
        record["artifact_role"] = "report_html"
        record["report_fields"] = extract_report_fields(path.read_text(encoding="utf-8", errors="replace"))
    elif suffix in {".icc", ".icm"}:
        record["artifact_role"] = "icc_profile"
        record["profile_fields"] = extract_icc_metadata(path)
    else:
        record["artifact_role"] = "inventory_only"
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for item in inventory_path(args.root):
        path = Path(str(item["path"]))
        if item["artifact_role"] in {"report_html", "icc_profile"}:
            enriched = item | extract_file(path)
        else:
            enriched = item
        records.append(enriched)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} records to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run extraction on local sample**

Run:

```powershell
python scripts\displaycal_extract.py "C:\Users\miles\AppData\Roaming\DisplayCAL\storage\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX" --out research\displaycal\extracted_records.json
```

Expected: local `.icm` metadata and any HTML reports in that folder are represented in JSON.

## Task 5: Hardware And Correction Research

**Files:**
- Create: `research/displaycal/correlation_report.md`
- Modify: `research/displaycal/extracted_records.json`

- [ ] **Step 1: Verify monitor model candidates from artifact names**

Start with these display model candidates:

```text
ASUS VZ249HEG1R
Acer SA241Y H
Built-in Retina Display
Display #1
PnP #2
Dell U2413
```

For each case, record:

```json
{
  "model": "ASUS VZ249HEG1R",
  "source_evidence": "artifact filename or report field",
  "manufacturer": "ASUS",
  "panel_type": "",
  "backlight_type": "",
  "native_resolution": "",
  "official_or_secondary_source_url": "",
  "confidence": "high|medium|low"
}
```

- [ ] **Step 2: Identify correction-file usage**

For each case, check whether files include `.ccss` or `.ccmx`.

Known local evidence to verify:

```text
Dell_U2413_25Jul12.ccss
```

Expected analysis questions:

```text
Does the selected correction match the actual display backlight technology?
Is the correction generic, vendor/model-specific, or mismatched?
Was the instrument likely an X-Rite i1D3-family colorimeter from DisplayCAL/Argyll naming?
Does the correction file explain better or worse report metrics across cases?
```

- [ ] **Step 3: Write correlation report**

`research/displaycal/correlation_report.md` must contain:

```markdown
# DisplayCAL Calibration Artifact Research

## Source Inventory

## Report Format Findings

## Quick Extraction Tool Fields

## Display Hardware Table

## Correction File Usage

## Cross-Case Correlations

## Unknowns And Next Checks
```

## Task 6: Validate And Review

**Files:**
- Verify: `scripts/*.py`
- Verify: `tests/*.py`
- Verify: `research/displaycal/*.json`
- Verify: `research/displaycal/correlation_report.md`

- [ ] **Step 1: Run syntax and tests**

Run:

```powershell
python -m compileall scripts tests
python -m pytest tests -q
```

Expected: no syntax errors; tests pass.

- [ ] **Step 2: Review outputs for privacy and publishability**

Check:

```text
No private customer planning notes are generated.
Drive URLs and local paths are included only as evidence for this local research workflow.
No files are deleted, moved, or uploaded.
```

- [ ] **Step 3: Final evidence summary**

Report:

```text
Plan path
Tools created
Inventory counts
Reports parsed
Profiles parsed
Confirmed display models/spec sources
Detected CCSS/CCMX usage
Remaining unknowns
```

## Self-Review

- Spec coverage: Covers Drive discovery, local DisplayCAL storage, report format research, quick key-field extraction tool, hardware/spec/backlight lookup, calibration device/correction usage, and cross-case correlation.
- Placeholder scan: No `TBD`, `TODO`, or vague task-only placeholders remain.
- Type consistency: Script names and function names are consistent across tasks.
- Risk boundary: The workflow is read-only against source artifacts and writes only derived research outputs under `Q:\Projects\Cal-panel`.
