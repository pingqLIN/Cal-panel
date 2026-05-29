from scripts.displaycal_report_parser import extract_report_fields


def test_extracts_displaycal_hidden_inputs_and_cgats_count() -> None:
    html = """
    <html>
      <head><title>Measurement Report 3.8.9.3 — VZ249HEG1R</title></head>
      <body>
        <h2 id="reporttitle">VZ249HEG1R @ 0, 0, 1920x1080 — 2023-08-25 15:54:56</h2>
        <input type="hidden" name="FF_display" value="VZ249HEG1R @ 0, 0, 1920x1080" />
        <input type="hidden" name="FF_instrument" value="i1 DisplayPro, ColorMunki Display — LCD (generic)" />
        <input type="hidden" name="FF_correction_matrix" value="i1 DisplayPro, ColorMunki Display &amp; ASUSTek COMPUTER INC VZ249HEG1R (i1 Pro 3).ccmx" />
        <input type="hidden" name="FF_profile" value="ColorGeek_ASUS VZ249HEG1R 2023-08-25 15-43 D6500 2.2 F-S XYZLUT+MTX" />
        <input type="hidden" name="FF_report_version" value="3.8.9.3" />
        <input type="hidden" name="FF_data_in" value="CTI3&#10;NUMBER_OF_FIELDS 4&#10;BEGIN_DATA_FORMAT&#10;SAMPLE_ID RGB_R RGB_G RGB_B&#10;END_DATA_FORMAT&#10;NUMBER_OF_SETS 1&#10;BEGIN_DATA&#10;1 100 100 100&#10;END_DATA" />
      </body>
    </html>
    """
    fields = extract_report_fields(html)
    assert fields["title"] == "Measurement Report 3.8.9.3 — VZ249HEG1R"
    assert fields["display"] == "VZ249HEG1R @ 0, 0, 1920x1080"
    assert fields["display_model"] == "VZ249HEG1R"
    assert fields["instrument"] == "i1 DisplayPro, ColorMunki Display — LCD (generic)"
    assert fields["correction_file"] == "i1 DisplayPro, ColorMunki Display & ASUSTek COMPUTER INC VZ249HEG1R (i1 Pro 3).ccmx"
    assert fields["correction_type"] == "ccmx"
    assert fields["profile"] == "ColorGeek_ASUS VZ249HEG1R 2023-08-25 15-43 D6500 2.2 F-S XYZLUT+MTX"
    assert fields["report_version"] == "3.8.9.3"
    assert fields["measurement_patch_count"] == 1
    assert fields["has_embedded_cgats"] is True
