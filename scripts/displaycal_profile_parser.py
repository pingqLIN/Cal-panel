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
        if tag_offset + tag_size <= len(data):
            tags[signature] = (tag_offset, tag_size)
        offset += 12
    return tags


def parse_text_tag(raw: bytes) -> str | None:
    if len(raw) < 8:
        return None
    tag_type = raw[:4].decode("latin1", errors="replace")
    if tag_type == "desc" and len(raw) >= 12:
        length = struct.unpack(">I", raw[8:12])[0]
        return raw[12 : 12 + max(length - 1, 0)].decode("ascii", errors="replace").strip("\x00").strip()
    if tag_type == "mluc" and len(raw) >= 28:
        count, record_size = struct.unpack(">II", raw[8:16])
        if count < 1 or record_size < 12:
            return None
        length, offset = struct.unpack(">II", raw[20:28])
        if offset + length > len(raw):
            return None
        return raw[offset : offset + length].decode("utf-16-be", errors="replace").strip("\x00").strip()
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
        text = parse_text_tag(data[offset : offset + size])
        if text:
            metadata[signature] = text
    return metadata
