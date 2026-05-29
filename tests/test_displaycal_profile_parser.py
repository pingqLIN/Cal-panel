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
