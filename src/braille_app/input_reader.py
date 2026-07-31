"""Readers that preserve the cell layout of text-based braille PDFs."""

import os
from io import BytesIO
from statistics import median

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
    rows = _group_rows(characters)
    if not rows:
        return []

    widths = [char["x1"] - char["x0"] for row in rows for char in row if char["x1"] > char["x0"]]
    if not widths:
        return []
    pitch = median(widths)
    left_edge = min(char["x0"] for row in rows for char in row)
    lines = []

    def rendered_cell(character):
        font_name = character.get("fontname", "").split("+")[-1]
        return font_maps.get(font_name, {}).get(character["text"], character["text"])

    for row in rows:
        row.sort(key=lambda char: char["x0"])
        raw_text = "".join(char["text"] for char in row)
        if "english (ueb)" in raw_text.lower():
            continue

        parts = [" " * max(0, round((row[0]["x0"] - left_edge) / pitch))]
        last_end = row[0]["x0"]
        for char in row:
            gap = max(0, round((char["x0"] - last_end) / pitch))
            if gap:
                parts.append(" " * gap)
            parts.append(rendered_cell(char))
            last_end = char["x1"]
        lines.append("".join(parts))
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
    mappings = {}
    for page_index, page in enumerate(reader.pages):
        resources = page.get("/Resources", {})
        for font_ref in resources.get("/Font", {}).values():
            font_object = font_ref.get_object()
            base_name = str(font_object.get("/BaseFont", "")).lstrip("/")
            if "braille" not in base_name.lower() or base_name in mappings:
                continue
            descriptor = font_object.get("/FontDescriptor")
            if descriptor is None and font_object.get("/DescendantFonts"):
                descriptor = font_object["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            if descriptor is None:
                continue
            descriptor = descriptor.get_object()
            font_file = descriptor.get("/FontFile2")
            if font_file is None:
                continue
            characters = {char["text"] for char in pages[page_index].chars if char.get("fontname", "").split("+")[-1] == base_name.split("+")[-1]}
            try:
                mappings[base_name.split("+")[-1]] = _font_dot_map(font_file.get_object().get_data(), characters)
            except Exception:
                # Keep text extraction as a safe fallback for PDFs without a
                # usable TrueType braille program.
                mappings[base_name.split("+")[-1]] = {}
    return mappings


def read_braille_input(file_path):
    """Read BRF/text or a text-based braille PDF into an ASCII-braille stream."""
    _, extension = os.path.splitext(file_path.lower())
    if extension == ".pdf":
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages = ["\n".join(_pdf_page_to_braille_lines(page.extract_words())) for page in pdf.pages]
        return _unicode_braille_to_ascii("\x0c".join(pages))
    with open(file_path, "r", encoding="utf-8", errors="ignore") as source:
        return _unicode_braille_to_ascii(source.read())
