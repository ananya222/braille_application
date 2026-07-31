import os
import re
import json
import logging
from docx import Document
import pdfplumber

# Configure logging
logger = logging.getLogger("DocExtractor")
logger.setLevel(logging.WARNING)

# =====================================================================
# CONFIGURATION & STYLE MAPPING BLOCK
# =====================================================================
# Duxbury Guess / Formatting assumptions:
# Standard DOCX paragraph styles and their mapping to our unified schema types.
STYLE_MAPPING = {
    "heading 1": "heading1",
    "heading 2": "heading2",
    "heading 3": "heading3",
    "heading 4": "heading4",
    "heading 5": "heading5",
    "heading 6": "heading6",
    "normal": "body",
    "body text": "body",
    "list bullet": "list_bullet",
    "list number": "list_number",
    "caption": "caption",
    "subtitle": "subtitle",
    "title": "title",
}

# Confirmed Spec: The output JSON structure must be:
# {
#   "pages": [
#     {
#       "print_page_number": int,
#       "blocks": [
#         {"type": "heading1"|"body"|"list_bullet"|"list_number"|"unknown", "text": str, "page_break_after": bool}
#       ]
#     }
#   ]
# }

# =====================================================================
# DOCX EXTRACTOR IMPLEMENTATION
# =====================================================================
class DocxExtractor:
    def __init__(self, style_mapping: dict = None):
        self.style_mapping = style_mapping or STYLE_MAPPING

    def extract(self, file_path: str) -> dict:
        doc = Document(file_path)
        pages = []
        current_page_number = 1
        current_blocks = []

        for p in doc.paragraphs:
            text = p.text.strip()
            has_break = self._has_page_break(p)

            # Handle empty or whitespace-only paragraphs explicitly —
            # include them in the output tagged as "empty" so nothing is silently dropped.
            if not text:
                style_name = p.style.name if p.style else "Normal"
                block = {
                    "type": "empty",
                    "text": "",
                    "page_break_after": has_break,
                    "raw_style": style_name
                }
                current_blocks.append(block)

                if has_break:
                    pages.append({
                        "print_page_number": current_page_number,
                        "blocks": current_blocks
                    })
                    current_blocks = []
                    current_page_number += 1
                continue

            # Check if paragraph has "page break before" property set
            if p.paragraph_format.page_break_before:
                if current_blocks:
                    pages.append({
                        "print_page_number": current_page_number,
                        "blocks": current_blocks
                    })
                    current_blocks = []
                current_page_number += 1

            # Determine paragraph style type
            style_name = p.style.name if p.style else "Normal"
            normalized_style = style_name.lower()
            
            block_type = "unknown"
            # Try exact mapping, then partial mapping (e.g. containing "heading" or "bullet")
            if normalized_style in self.style_mapping:
                block_type = self.style_mapping[normalized_style]
            elif "heading 1" in normalized_style:
                block_type = "heading1"
            elif "heading 2" in normalized_style:
                block_type = "heading2"
            elif "heading" in normalized_style:
                block_type = "heading3"
            elif "bullet" in normalized_style:
                block_type = "list_bullet"
            elif "number" in normalized_style:
                block_type = "list_number"
            else:
                # Defensive warning for unknown styles
                logger.warning(f"Unknown DOCX style: '{style_name}' for paragraph: '{text[:30]}...'")
                block_type = "unknown"


            block = {
                "type": block_type,
                "text": text,
                "page_break_after": has_break,
                "raw_style": style_name
            }
            current_blocks.append(block)

            if has_break:
                # Yield current page, start new one
                pages.append({
                    "print_page_number": current_page_number,
                    "blocks": current_blocks
                })
                current_blocks = []
                current_page_number += 1

        # Append last remaining page
        if current_blocks or not pages:
            pages.append({
                "print_page_number": current_page_number,
                "blocks": current_blocks
            })

        return {"pages": pages}

    def _has_page_break(self, paragraph) -> bool:
        """
        Detects if a paragraph contains an explicit page break (w:br w:type="page")
        or a last rendered page break (w:lastRenderedPageBreak) in its XML elements.
        """
        # Look for break element in runs
        p_element = paragraph._p
        
        # Check for w:br w:type="page"
        for br in p_element.xpath('.//w:br'):
            if br.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type') == 'page':
                return True
                
        # Check for w:lastRenderedPageBreak
        if p_element.xpath('.//w:lastRenderedPageBreak'):
            return True
            
        return False


# =====================================================================
# PDF EXTRACTOR IMPLEMENTATION
# =====================================================================
class PdfExtractor:
    def __init__(self):
        pass

    def extract(self, file_path: str) -> dict:
        pages = []
        
        with pdfplumber.open(file_path) as pdf:
            for idx, pdf_page in enumerate(pdf.pages, start=1):
                blocks = []
                
                # Extract words with layout metadata (font size, weight, etc.)
                words = pdf_page.extract_words()
                
                if not words:
                    pages.append({
                        "print_page_number": idx,
                        "blocks": []
                    })
                    continue
                
                # Group words into lines based on their vertical top coordinate (tolerance +/- 3 pixels)
                lines = self._group_words_to_lines(words)
                
                for line_text, font_size, is_bold in lines:
                    text = line_text.strip()
                    if not text:
                        continue
                    
                    # Duxbury Guess: Visual classification of PDF blocks
                    block_type = "body"
                    
                    # Classify based on font size and formatting
                    if font_size >= 16:
                        block_type = "heading1"
                    elif font_size >= 13:
                        block_type = "heading2"
                    elif is_bold and font_size >= 11:
                        block_type = "heading3"
                    elif text.startswith(('•', '▪', '-', '*')):
                        block_type = "list_bullet"
                        # Clean up bullet symbol from text for cleaner comparison if needed
                        text = re.sub(r'^[•▪\-*]\s*', '', text)
                    elif re.match(r'^\d+[\.\)]\s+', text):
                        block_type = "list_number"
                        # Clean up list number from text
                        text = re.sub(r'^\d+[\.\)]\s*', '', text)
                    
                    blocks.append({
                        "type": block_type,
                        "text": text,
                        "page_break_after": False  # PDF has implicit page boundaries, not inline breaks
                    })
                
                # Tag the last block of the page as page_break_after = True
                if blocks:
                    blocks[-1]["page_break_after"] = True
                    
                pages.append({
                    "print_page_number": idx,
                    "blocks": blocks
                })
                
        return {"pages": pages}

    def _group_words_to_lines(self, words: list) -> list:
        """
        Groups list of PDF words into lines based on vertical tolerance.
        Returns a list of tuples: (line_text, avg_font_size, is_bold)
        """
        # Sort words top-to-bottom, then left-to-right
        words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        
        lines_data = []
        current_line_words = []
        current_top = None
        
        tolerance = 3.0  # vertical pixels tolerance for words on same line
        
        for w in words:
            top = w["top"]
            
            if current_top is None:
                current_top = top
                current_line_words.append(w)
            elif abs(top - current_top) <= tolerance:
                current_line_words.append(w)
            else:
                # Process finished line
                lines_data.append(self._process_line_words(current_line_words))
                current_line_words = [w]
                current_top = top
                
        if current_line_words:
            lines_data.append(self._process_line_words(current_line_words))
            
        return lines_data

    def _process_line_words(self, line_words: list) -> tuple:
        """
        Helper to construct a text line from grouped words and compute average font characteristics.
        """
        # Sort left to right
        line_words = sorted(line_words, key=lambda w: w["x0"])
        line_text = " ".join(w["text"] for w in line_words)
        
        # Calculate average font size
        sizes = [float(w.get("size", 10.0)) for w in line_words]
        avg_size = sum(sizes) / len(sizes) if sizes else 10.0
        
        # Check if text is bold
        bold_indicators = ["bold", "bd", "heavy", "black"]
        bold_count = sum(1 for w in line_words if any(bi in w.get("fontname", "").lower() for bi in bold_indicators))
        is_bold = bold_count > (len(line_words) / 2)
        
        return line_text, avg_size, is_bold


# =====================================================================
# UNIFIED DOCUMENT EXTRACTOR CLASS
# =====================================================================
class DocumentExtractor:
    def __init__(self, style_mapping: dict = None):
        self.docx_extractor = DocxExtractor(style_mapping)
        self.pdf_extractor = PdfExtractor()

    def extract(self, file_path: str) -> dict:
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".docx":
            return self.docx_extractor.extract(file_path)
        elif ext == ".pdf":
            return self.pdf_extractor.extract(file_path)
        else:
            raise ValueError(f"Unsupported document format: {ext}. Only .docx and .pdf are supported.")
