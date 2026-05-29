from pathlib import Path

from scripts.displaycal_correction_parser import extract_correction_metadata


LOCAL_CORRECTION = Path(
    r"C:\Users\miles\AppData\Roaming\DisplayCAL\storage\PnP #2 2026-05-27 17-51 0.3127x 0.329y 2.2 F-S XYZLUT+MTX"
    r"\Dell_U2413_25Jul12.ccss"
)


def test_extracts_local_ccss_metadata_when_available() -> None:
    if not LOCAL_CORRECTION.exists():
        return
    metadata = extract_correction_metadata(LOCAL_CORRECTION)
    assert metadata["correction_type"] == "ccss"
    assert metadata["display"] == "Dell U2413"
    assert "technology" in metadata
