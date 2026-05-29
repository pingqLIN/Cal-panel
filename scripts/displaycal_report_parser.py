from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re


FIELD_ALIASES = {
    "adaption": "adaptation",
    "blackpoint": "blackpoint_xyz",
    "correction_matrix": "correction_file",
    "data_in": "measurement_data",
    "data_ref": "reference_data",
    "datetime": "measurement_datetime",
    "display": "display",
    "instrument": "instrument",
    "profile": "profile",
    "profile_whitepoint": "profile_whitepoint_xyz",
    "profile_whitepoint_normalized": "profile_whitepoint_normalized_xyz",
    "report_version": "report_version",
    "testchart": "testchart",
    "whitepoint": "whitepoint_xyz",
    "whitepoint_normalized": "whitepoint_normalized_xyz",
}


class DisplaycalHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.in_report_title = False
        self.title_parts: list[str] = []
        self.report_title_parts: list[str] = []
        self.hidden_inputs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        attrs_dict = {name.casefold(): value or "" for name, value in attrs}
        if tag == "title":
            self.in_title = True
        if tag == "h2" and attrs_dict.get("id") == "reporttitle":
            self.in_report_title = True
        if tag == "input" and attrs_dict.get("type", "").casefold() == "hidden":
            name = attrs_dict.get("name", "")
            if name.startswith("FF_"):
                self.hidden_inputs[name] = attrs_dict.get("value", "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
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
    return re.sub(r"\s+", " ", unescape(value)).strip()


def normalize_key(value: str) -> str:
    key = normalize_text(value).casefold().rstrip(":")
    key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return FIELD_ALIASES.get(key, key)


def infer_display_model(display: str) -> str:
    value = display.split("@", 1)[0].strip()
    return re.sub(r"\s+", " ", value)


def infer_correction_type(correction_file: str) -> str:
    lowered = correction_file.casefold()
    if ".ccmx" in lowered:
        return "ccmx"
    if ".ccss" in lowered:
        return "ccss"
    if correction_file:
        return "unknown"
    return ""


def count_cgats_sets(payload: str) -> int | None:
    match = re.search(r"(?im)^\s*NUMBER_OF_SETS\s+(\d+)\s*$", payload)
    if not match:
        return None
    return int(match.group(1))


def extract_report_fields(html: str, *, include_payloads: bool = False) -> dict[str, object]:
    parser = DisplaycalHtmlParser()
    parser.feed(html)

    fields: dict[str, object] = {}
    title = normalize_text(" ".join(parser.title_parts))
    if title:
        fields["title"] = title
    report_title = normalize_text(" ".join(parser.report_title_parts))
    if report_title:
        fields["report_title"] = report_title

    payload_fields: dict[str, str] = {}
    for raw_key, raw_value in parser.hidden_inputs.items():
        key = normalize_key(raw_key.removeprefix("FF_"))
        value = unescape(raw_value).replace("\r\n", "\n")
        if key in {"measurement_data", "reference_data"}:
            payload_fields[key] = value
            if include_payloads:
                fields[key] = value
            patch_count = count_cgats_sets(value)
            if patch_count is not None:
                count_key = "measurement_patch_count" if key == "measurement_data" else "reference_patch_count"
                fields[count_key] = patch_count
        else:
            fields[key] = normalize_text(value)

    display = str(fields.get("display", ""))
    if display:
        fields["display_model"] = infer_display_model(display)
    correction_file = str(fields.get("correction_file", ""))
    if correction_file:
        fields["correction_type"] = infer_correction_type(correction_file)
    if "measurement_data" in payload_fields or "reference_data" in payload_fields:
        fields["has_embedded_cgats"] = True
    return fields
