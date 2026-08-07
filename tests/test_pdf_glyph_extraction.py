import os
import sys
import pdfplumber

# Ensure src and vendor modules are in path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(base_dir, "vendor", "liblouis-bindings"))
sys.path.insert(0, os.path.join(base_dir, "src"))

from braille_app.input_reader import (
    read_braille_input,
    _embedded_braille_font_maps,
    _pdf_page_to_braille_lines_from_chars
)

def _find_doc1_pdf():
    """Locate Document-1 Open Braille PDF regardless of exact directory layout."""
    # Preferred: testfiles/Document 1 inside the project
    _d = os.path.join(base_dir, "testfiles", "Document 1")
    if os.path.isdir(_d):
        for f in os.listdir(_d):
            if f.endswith(".pdf") and "Document-1" in f and "Open Braille" in f:
                return os.path.join(_d, f)
    # Fallback: walk known external testfiles root
    _ext = r"O:\testfiles_braille"
    if os.path.isdir(_ext):
        for root, dirs, files in os.walk(_ext):
            if "Open Braille" in root:
                for f in files:
                    if f.endswith(".pdf") and "Document-1" in f and "Open Braille" in f:
                        return os.path.join(root, f)
    return None

pdf_path = _find_doc1_pdf()

def test_embedded_glyph_extraction():
    # Test 1: Embedded glyph extraction of '~' maps to U+2818 ('⠘')
    with pdfplumber.open(pdf_path) as pdf:
        font_maps = _embedded_braille_font_maps(pdf, pdf.pages)
        # Find 'Braille' font mapping
        braille_font_map = None
        for font_name, mapping in font_maps.items():
            if "braille" in font_name.lower():
                braille_font_map = mapping
                break
        assert braille_font_map is not None, "Could not locate Braille font map"
        assert braille_font_map.get("~") == "⠘"
        assert ord(braille_font_map["~"]) == 0x2818

def test_unicode_preservation():
    # Test 2: Unicode preservation (U+2818 remains '⠘' in the output, does not become '^')
    res = read_braille_input(pdf_path)
    assert "^" not in res, "Unicode braille was reverse-mapped to ASCII caret '^'"
    assert "⠘" in res, "Unicode braille '⠘' is missing from output"

def test_ordinary_cells():
    # Test 3: Ordinary cells (evaluation extracts as U+2811 U+2827 U+2801 U+2807 U+2825 U+2801 U+281E U+280A U+2815 U+281D)
    res = read_braille_input(pdf_path)
    expected_cells = "⠑⠧⠁⠇⠥⠁⠞⠊⠕⠝"
    assert expected_cells in res, f"Expected word '{expected_cells}' not found in PDF extraction"

def test_known_visual_error_preservation():
    # Test 4: Known visual error preservation (Page 3 CPI parentheses visually render as '⠈⠣' / '⠈⠜')
    res = read_braille_input(pdf_path)
    assert "⠈⠣" in res, "Visual error for opening parenthesis not preserved"
    assert "⠈⠜" in res, "Visual error for closing parenthesis not preserved"

def test_production_integration():
    # Test 5: read_braille_input returns glyph-aware Unicode Braille
    res = read_braille_input(pdf_path)
    assert isinstance(res, str)
    # Unicode Braille character range check
    unicode_range_chars = [c for c in res if 0x2800 <= ord(c) <= 0x28FF]
    assert len(unicode_range_chars) > 0, "No Unicode Braille cells found in output"

def test_brf_txt_regression():
    # Test 7: Verify that existing BRF/TXT behavior is unchanged (returns ASCII Braille)
    mock_brf_content = ",hello _w6"
    temp_brf_path = os.path.join(base_dir, "tests", "output", "temp_regression.brf")
    os.makedirs(os.path.dirname(temp_brf_path), exist_ok=True)
    with open(temp_brf_path, "w", encoding="utf-8") as f:
        f.write(mock_brf_content)
    
    try:
        res = read_braille_input(temp_brf_path)
        assert res == ",hello _w6", f"BRF reader changed: expected ',hello _w6', got {repr(res)}"
    finally:
        if os.path.exists(temp_brf_path):
            os.remove(temp_brf_path)

def test_font_identity_collision():
    from unittest.mock import MagicMock, patch

    font_f1_file = MagicMock()
    font_f1_file.get_object().get_data.return_value = b"font_a"
    descriptor_f1 = MagicMock()
    descriptor_f1.get_object.return_value = {
        "/FontFile2": font_f1_file
    }
    font_f1 = MagicMock()
    font_f1.get_object.return_value = {
        "/BaseFont": "/AAAAAA+Braille",
        "/FontDescriptor": descriptor_f1
    }
    
    font_f2_file = MagicMock()
    font_f2_file.get_object().get_data.return_value = b"font_b"
    descriptor_f2 = MagicMock()
    descriptor_f2.get_object.return_value = {
        "/FontFile2": font_f2_file
    }
    font_f2 = MagicMock()
    font_f2.get_object.return_value = {
        "/BaseFont": "/BBBBBB+Braille",
        "/FontDescriptor": descriptor_f2
    }
    
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.get.return_value = {
        "/Font": {
            "/F1": font_f1,
            "/F2": font_f2
        }
    }
    mock_reader.pages = [mock_page]
    
    mock_pdfplumber_page = MagicMock()
    mock_pdfplumber_page.chars = [
        {"text": "x", "fontname": "AAAAAA+Braille"},
        {"text": "x", "fontname": "BBBBBB+Braille"}
    ]
    
    mock_pdf = MagicMock()
    mock_pdf.stream.name = "dummy.pdf"
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        with patch("braille_app.input_reader._font_dot_map") as mock_dot_map:
            def side_effect(font_data, characters):
                if font_data == b"font_a":
                    return {"x": "⠁"}
                if font_data == b"font_b":
                    return {"x": "⠃"}
                return {}
            mock_dot_map.side_effect = side_effect
            
            mappings = _embedded_braille_font_maps(mock_pdf, [mock_pdfplumber_page])
            
            # Assertions to ensure Font A and Font B are kept isolated
            assert mappings.get("AAAAAA+Braille", {}).get("x") == "⠁", f"Font A mapped incorrectly: got {mappings.get('AAAAAA+Braille')}"
            assert mappings.get("BBBBBB+Braille", {}).get("x") == "⠃", f"Font B mapped incorrectly: got {mappings.get('BBBBBB+Braille')}"


def test_provenance_record():
    # Test 1 — provenance record
    pdf_path = _find_doc1_pdf()
    from braille_app.input_reader import read_braille_pdf_with_provenance
    res = read_braille_pdf_with_provenance(pdf_path)
    
    first_word_prov = res.word_provenance[0]
    assert len(first_word_prov) > 0
    record = first_word_prov[0]
    assert record.page == 1
    assert record.x0 > 0
    assert record.x1 > record.x0
    assert record.top > 0
    assert record.bottom > record.top
    assert record.source_char == "~"
    assert record.unicode_cell == "⠘"
    assert record.fontname == "BCDEEE+Braille"
    assert record.color is not None


def test_normalized_word_alignment():
    # Test 2 — normalized word alignment
    pdf_path = _find_doc1_pdf()
    from braille_app.input_reader import read_braille_pdf_with_provenance
    from braille_app.diff_engine import DiffEngine
    res = read_braille_pdf_with_provenance(pdf_path)
    diff_engine = DiffEngine()
    actual_normalized = diff_engine._normalize_braille_stream(res.content, strip_page_numbers=True, is_actual=True)
    actual_words = actual_normalized.split()
    
    assert len(actual_words) == len(res.word_provenance)
    for k, prov_list in enumerate(res.word_provenance):
        reconstructed = "".join(p.unicode_cell for p in prov_list)
        expected_w = actual_words[k]
        norm_reconstructed = reconstructed.replace('\u2824', '-').replace('\u2011', '-')
        assert norm_reconstructed == expected_w


def test_provenance_resolver_scenarios():
    from braille_app.input_reader import PdfCellProvenance
    from braille_app.provenance_resolver import resolve_mismatch_provenance

    # Test 3: replacement
    p_a = PdfCellProvenance(1, 10, 15, 10, 15, "a", "⠁", "font", None)
    p_x = PdfCellProvenance(1, 20, 25, 10, 15, "x", "⠭", "font", None)
    p_c = PdfCellProvenance(1, 30, 35, 10, 15, "c", "⠉", "font", None)
    word_prov = [[p_a, p_x, p_c]]
    
    diff_record = {
        "type": "character_mismatch",
        "expected": "⠁⠃⠉",
        "actual": "⠁⠭⠉",
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1
    }
    res = resolve_mismatch_provenance(diff_record, word_prov)
    assert res["kind"] == "cell_replace"
    assert len(res["cells"]) == 1
    assert res["cells"][0] == p_x

    # Test 4: insertion
    p_b = PdfCellProvenance(1, 30, 35, 10, 15, "b", "⠃", "font", None)
    p_c2 = PdfCellProvenance(1, 40, 45, 10, 15, "c", "⠉", "font", None)
    word_prov_ins = [[p_a, p_x, p_b, p_c2]]
    diff_record_ins = {
        "type": "character_mismatch",
        "expected": "⠁⠃⠉",
        "actual": "⠁⠭⠃⠉",
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1
    }
    res_ins = resolve_mismatch_provenance(diff_record_ins, word_prov_ins)
    assert res_ins["kind"] == "cell_insert"
    assert len(res_ins["cells"]) == 1
    assert res_ins["cells"][0] == p_x

    # Test 5: deletion
    word_prov_del = [[p_a, p_c]]
    diff_record_del = {
        "type": "character_mismatch",
        "expected": "⠁⠃⠉",
        "actual": "⠁⠉",
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1
    }
    res_del = resolve_mismatch_provenance(diff_record_del, word_prov_del)
    assert res_del["kind"] == "cell_delete"
    assert res_del["previous"] == p_a
    assert res_del["next"] == p_c

    # Test 6: multi-cell replacement
    p_y = PdfCellProvenance(1, 25, 29, 10, 15, "y", "⠽", "font", None)
    word_prov_multi = [[p_a, p_x, p_y, p_c2]]
    diff_record_multi = {
        "type": "word_mismatch",
        "expected": "⠁⠃⠉",
        "actual": "⠁⠭⠽⠉",
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1
    }
    res_multi = resolve_mismatch_provenance(diff_record_multi, word_prov_multi)
    assert res_multi["kind"] in ("replacement", "cell_replace")
    assert p_x in res_multi["cells"]
    assert p_y in res_multi["cells"]

    # Test 7: document start deletion
    word_prov_start = [[p_a]]
    diff_record_start = {
        "type": "deletion",
        "expected": "⠃",
        "actual": "",
        "actual_start_idx": 0,
        "actual_end_idx": 0,
        "expected_start_idx": 0,
        "expected_end_idx": 1
    }
    res_start = resolve_mismatch_provenance(diff_record_start, word_prov_start)
    assert res_start["kind"] == "gap"
    assert res_start["previous"] is None
    assert res_start["next"] == p_a

    # Test 8: document end deletion
    diff_record_end = {
        "type": "deletion",
        "expected": "⠃",
        "actual": "",
        "actual_start_idx": 1,
        "actual_end_idx": 1,
        "expected_start_idx": 1,
        "expected_end_idx": 2
    }
    res_end = resolve_mismatch_provenance(diff_record_end, word_prov_start)
    assert res_end["kind"] == "gap"
    assert res_end["previous"] == p_a
    assert res_end["next"] is None


def test_cross_line_cross_page_provenance():
    # Test 9 and Test 10: Cross-line and Cross-page provenance
    pdf_path = _find_doc1_pdf()
    from braille_app.input_reader import read_braille_pdf_with_provenance
    res = read_braille_pdf_with_provenance(pdf_path)
    
    found_p2 = False
    for prov_list in res.word_provenance:
        for p in prov_list:
            if p.page == 2:
                found_p2 = True
                break
    assert found_p2, "Page 2 cells were not mapped to page 2"


def test_read_braille_input_compatibility():
    # Test 11: read_braille_input compatibility
    pdf_path = _find_doc1_pdf()
    from braille_app.input_reader import read_braille_input
    import hashlib
    res = read_braille_input(pdf_path)
    h = hashlib.sha256(res.encode('utf-8')).hexdigest()
    assert h == "9d64a7919d1ada708677f7a7ebef35e88435c740f06ae4d1cb8ea4e43bcbcf62"


def test_brf_txt_compatibility():
    # Test 12: BRF/TXT compatibility
    temp_brf_path = r"O:\braille_0.2\tests\output\temp_test.brf"
    os.makedirs(os.path.dirname(temp_brf_path), exist_ok=True)
    with open(temp_brf_path, "w", encoding="utf-8") as f:
        f.write("⠠⠓⠑⠇⠇⠕")
        
    try:
        from braille_app.input_reader import read_braille_input
        res = read_braille_input(temp_brf_path)
        assert res == ",HELLO"
    finally:
        if os.path.exists(temp_brf_path):
            os.remove(temp_brf_path)

