"""Readers that preserve the cell layout of text-based braille PDFs."""

import os
from io import BytesIO
from statistics import median
from dataclasses import dataclass

from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE


def _group_rows(words):
    """Group by observed baselines; PDF line pitch must never be assumed."""
    rows = []
    for word in sorted(words, key=lambda item: (item["top"], item["x0"])):
        if not rows or abs(word["top"] - rows[-1][0]["top"]) > 2.0:
            rows.append([word])
        else:
            rows[-1].append(word)
    return rows


def _pdf_page_to_braille_lines(words):
    rows = _group_rows(words)
    if not rows:
        return []
    widths = [
        (word["x1"] - word["x0"]) / len(word["text"])
        for row in rows for word in row if word["text"]
    ]
    pitch = median(widths)
    left_edge = min(word["x0"] for row in rows for word in row)
    lines = []
    for row in rows:
        row.sort(key=lambda item: item["x0"])
        if "english (ueb)" in " ".join(item["text"] for item in row).lower():
            continue  # print running header, not braille content
        parts = [" " * max(0, round((row[0]["x0"] - left_edge) / pitch))]
        last_end = row[0]["x0"]
        for index, word in enumerate(row):
            if index:
                # Quantize omitted PDF whitespace using the measured cell pitch.
                parts.append(" " * max(1, round((word["x0"] - last_end) / pitch)))
            parts.append(word["text"])
            last_end = word["x1"]
        lines.append("".join(parts))
    return lines


def _pdf_page_to_braille_lines_from_chars(characters, font_maps):
    """Rebuild PDF lines from rendered glyphs, not merely PDF text codes.

    Duxbury PDFs can retain a plausible text code even where a font glyph
    renders different Braille dots.  Reading the embedded font's dot pattern
    lets comparison detect that error whether the glyph is black or coloured.
    """
    lines, _ = _pdf_page_to_braille_lines_from_chars_with_provenance(characters, font_maps, 1)
    return lines


def _unicode_braille_to_ascii(text):
    reverse = {value: key for key, value in ASCII_TO_UNICODE_BRAILLE.items()}
    reverse["\u2800"] = " "
    return "".join(reverse.get(char, char) for char in text)


def _connected_dot_centres(font, character):
    """Return centres of the raised-dot blobs in one embedded font glyph."""
    mask = font.getmask(character)
    width, height = mask.size
    pixels = list(mask)
    seen = set()
    centres = []
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if index in seen or pixels[index] <= 127:
                continue
            queue = [(x, y)]
            seen.add(index)
            component = []
            while queue:
                current_x, current_y = queue.pop()
                component.append((current_x, current_y))
                for next_x, next_y in ((current_x + 1, current_y), (current_x - 1, current_y), (current_x, current_y + 1), (current_x, current_y - 1)):
                    next_index = next_y * width + next_x
                    if 0 <= next_x < width and 0 <= next_y < height and next_index not in seen and pixels[next_index] > 127:
                        seen.add(next_index)
                        queue.append((next_x, next_y))
            if len(component) >= 4:
                centres.append((sum(point[0] for point in component) / len(component), sum(point[1] for point in component) / len(component)))
    return centres


def _cluster_axis(values, expected_clusters):
    """Return representative centres for a small, well-separated dot axis."""
    values = sorted(values)
    groups = []
    for value in values:
        if not groups or abs(value - groups[-1][-1]) > 8:
            groups.append([value])
        else:
            groups[-1].append(value)
    centres = [sum(group) / len(group) for group in groups]
    return centres if len(centres) == expected_clusters else []


def _font_dot_map(font_data, characters):
    """Build a Unicode-braille map from the *rendered* embedded font glyphs."""
    from PIL import ImageFont

    font = ImageFont.truetype(BytesIO(font_data), 220)
    glyph_dots = {character: _connected_dot_centres(font, character) for character in characters}
    x_axis = _cluster_axis([x for dots in glyph_dots.values() for x, _ in dots], 2)
    y_axis = _cluster_axis([y for dots in glyph_dots.values() for _, y in dots], 3)
    if len(x_axis) != 2 or len(y_axis) != 3:
        return {}

    result = {}
    for character, dots in glyph_dots.items():
        pattern = 0
        for x, y in dots:
            column = min(range(2), key=lambda index: abs(x_axis[index] - x))
            row = min(range(3), key=lambda index: abs(y_axis[index] - y))
            dot_number = row + 1 if column == 0 else row + 4
            pattern |= 1 << (dot_number - 1)
        result[character] = chr(0x2800 + pattern)
    return result


def _embedded_braille_font_maps(pdf, pages):
    """Read embedded Braille fonts and map PDF text codes to visible dot cells."""
    from pypdf import PdfReader

    reader = PdfReader(pdf.stream.name)
    font_chars = {}
    font_files = {}

    for page_index, page in enumerate(reader.pages):
        resources = page.get("/Resources", {})
        for font_ref in resources.get("/Font", {}).values():
            font_object = font_ref.get_object()
            base_name = str(font_object.get("/BaseFont", "")).lstrip("/")
            if "braille" not in base_name.lower():
                continue
            
            font_id = base_name
            descriptor = font_object.get("/FontDescriptor")
            if descriptor is None and font_object.get("/DescendantFonts"):
                descriptor = font_object["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            if descriptor:
                descriptor = descriptor.get_object()
                font_file = descriptor.get("/FontFile2")
                if font_file:
                    font_files[font_id] = font_file.get_object().get_data()

            page_chars = {
                char["text"] for char in pages[page_index].chars 
                if char.get("fontname", "") == font_id
            }
            font_chars.setdefault(font_id, set()).update(page_chars)

    mappings = {}
    for font_short, characters in font_chars.items():
        font_data = font_files.get(font_short)
        if font_data:
            try:
                mappings[font_short] = _font_dot_map(font_data, characters)
            except Exception:
                mappings[font_short] = {}
        else:
            mappings[font_short] = {}

    return mappings


def read_braille_input(file_path):
    """Read BRF/text or a text-based braille PDF into an ASCII-braille stream."""
    _, extension = os.path.splitext(file_path.lower())
    if extension == ".pdf":
        return read_braille_pdf_with_provenance(file_path).content
    with open(file_path, "r", encoding="utf-8", errors="ignore") as source:
        return _unicode_braille_to_ascii(source.read())


@dataclass
class PdfCellProvenance:
    page: int
    x0: float
    x1: float
    top: float
    bottom: float
    source_char: str
    unicode_cell: str
    fontname: str
    color: object


@dataclass
class PdfBrailleInput:
    content: str
    word_provenance: list


def _pdf_page_to_braille_lines_from_chars_with_provenance(characters, font_maps, page_idx):
    from statistics import median
    rows = _group_rows(characters)
    if not rows:
        return [], []
    widths = [
        (char["x1"] - char["x0"])
        for row in rows for char in row if char["x1"] > char["x0"]
    ]
    if not widths:
        return [], []
    pitch = median(widths)
    left_edge = min(char["x0"] for row in rows for char in row)
    lines = []
    line_provenance = []

    def rendered_cell(character):
        if character["text"].isspace():
            return "\u2800" if character["text"] == " " else character["text"]
            
        font_name = character.get("fontname", "")
        is_braille_font = "braille" in font_name.lower()
        mapping = font_maps.get(font_name, {})
        if is_braille_font:
            if not mapping:
                raise ValueError(f"Failed to load embedded Braille font program for {font_name}")
            if character["text"] not in mapping:
                raise ValueError(f"Missing glyph mapping for character {repr(character['text'])} in font {font_name}")
            return mapping[character["text"]]
        return character["text"]

    for row in rows:
        row.sort(key=lambda char: char["x0"])
        raw_text = "".join(char["text"] for char in row)
        if "english (ueb)" in raw_text.lower():
            continue

        parts = []
        prov = []
        indent_spaces = max(0, round((row[0]["x0"] - left_edge) / pitch))
        for _ in range(indent_spaces):
            parts.append(" ")
            prov.append(None)
            
        last_end = row[0]["x0"]
        for char in row:
            gap = max(0, round((char["x0"] - last_end) / pitch))
            for _ in range(gap):
                parts.append(" ")
                prov.append(None)
            cell = rendered_cell(char)
            parts.append(cell)
            color = char.get("non_stroking_color") or char.get("stroking_color")
            prov.append(PdfCellProvenance(
                page=page_idx,
                x0=char["x0"],
                x1=char["x1"],
                top=char["top"],
                bottom=char["bottom"],
                source_char=char["text"],
                unicode_cell=cell,
                fontname=char.get("fontname", ""),
                color=color
            ))
            last_end = char["x1"]
        lines.append("".join(parts))
        line_provenance.append(prov)
    return lines, line_provenance


def _normalize_and_track_provenance(content, prov_map):
    import re
    from braille_app.diff_engine import DiffEngine
    
    diff_engine = DiffEngine()
    actual_normalized = diff_engine._normalize_braille_stream(content, strip_page_numbers=True, is_actual=True)
    expected_words = actual_normalized.split()
    
    start_offset = 0
    lstrip_len = len(content) - len(content.lstrip())
    start_offset += lstrip_len
    
    stripped_text = content.lstrip()
    match = re.match(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', stripped_text)
    if match:
        start_offset += match.end()
        
    pages = content.split('\x0c')
    page_start_idx = 0
    
    word_provenance = []
    
    for page in pages:
        lines = page.replace('\r\n', '\n').split('\n')
        line_start_idx = page_start_idx
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                word_chars = []
                word_provs = []
                for c_idx, char in enumerate(line):
                    orig_idx = line_start_idx + c_idx
                    if orig_idx < start_offset:
                        continue
                    if char == ' ' or char == '\u2800':
                        if word_chars:
                            word_provenance.append(word_provs)
                            word_chars = []
                            word_provs = []
                    else:
                        word_chars.append(char)
                        p_val = prov_map[orig_idx]
                        if p_val is not None:
                            word_provs.append(p_val)
                if word_chars:
                    word_provenance.append(word_provs)
                    
            line_start_idx += len(line) + 1
        page_start_idx += len(page) + 1
        
    assert len(expected_words) == len(word_provenance), f"Invariant A failed: len(expected_words)={len(expected_words)} != len(word_provenance)={len(word_provenance)}"
    
    for k, prov_list in enumerate(word_provenance):
        reconstructed = "".join(p.unicode_cell for p in prov_list if p is not None)
        expected_w = expected_words[k]
        norm_reconstructed = reconstructed.replace('\u2824', '-').replace('\u2011', '-')
        assert norm_reconstructed == expected_w, f"Invariant B failed at word {k}: expected {repr(expected_w)}, got {repr(norm_reconstructed)}"
        
    return word_provenance


def read_braille_pdf_with_provenance(file_path):
    """Read a text-based braille PDF and return PdfBrailleInput with cell provenance."""
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        has_chars = any(len(page.chars) > 0 for page in pdf.pages)
        if not has_chars:
            raise ValueError("Scanned PDF or PDF without vector text characters is not supported.")
        font_maps = _embedded_braille_font_maps(pdf, pdf.pages)
        
        global_text = []
        global_provenance = []
        
        for page_idx, page in enumerate(pdf.pages, start=1):
            lines, line_prov = _pdf_page_to_braille_lines_from_chars_with_provenance(page.chars, font_maps, page_idx)
            page_text = "\n".join(lines)
            page_prov = []
            for i, line_p in enumerate(line_prov):
                page_prov.extend(line_p)
                if i < len(line_prov) - 1:
                    page_prov.append(None)
            global_text.append(page_text)
            global_provenance.append(page_prov)
            
        content = "\x0c".join(global_text)
        full_provenance = []
        for i, page_p in enumerate(global_provenance):
            full_provenance.extend(page_p)
            if i < len(global_provenance) - 1:
                full_provenance.append(None)
                
        word_provenance = _normalize_and_track_provenance(content, full_provenance)
        
        return PdfBrailleInput(content=content, word_provenance=word_provenance)
