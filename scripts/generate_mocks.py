import os
from pathlib import Path
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_mock_docx(dest_path: str):
    doc = Document()
    doc.add_heading("The Great Adventure", level=1)
    doc.add_paragraph("This is a simple test sentence for verification.")
    doc.add_paragraph("He was very quick to run home after a long stormy night.")
    doc.save(dest_path)
    print(f"[OK] Generated mock English DOCX file: {os.path.abspath(dest_path)}")

def create_mock_braille_pdf(dest_path: str):
    # Translated with liblouis en-ueb-g2.ctb:
    # "The Great Adventure" -> ",! ,grt ,adv5ture"
    # "This is a simple test sentence for verification." -> ",? is a simple te/ s5t;e = v;ifict5."
    # "He was very quick to run home after a long stormy night." -> ",he wd v quick to run h aft a l stormy ni<t."
    pages_text = [
        [
            "",
            "  ,! ,grt ,adv5ture",
            "",
            "  ,? is a simple te/ s5t;e = v;ifict5.",
            "",
            "  ,he wd v quick to run h aft a l stormy ni<t.",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                                     #a"
        ]
    ]

    c = canvas.Canvas(dest_path, pagesize=letter)
    width, height = letter
    
    for page_lines in pages_text:
        c.setFont("Courier", 11)
        y = height - 54
        for line in page_lines:
            c.drawString(54, y, line)
            y -= 14
        c.showPage()
        
    c.save()
    print(f"[OK] Generated mock Braille PDF file: {os.path.abspath(dest_path)}")

def create_mismatch_braille_pdf(dest_path: str):
    # Realistic Braille errors:
    # 1. Translation typo in paragraph 1: ",? is a simple test s5t;e" (missed UEB "te/" contraction for "test")
    # 2. Omitted word in paragraph 2: ",he wd v quick to run aft a l stormy ni<t." (omitted the word "home" / "h")
    # 3. Heading layout offset (heading indent 4 spaces instead of 2)
    pages_text = [
        [
            "",
            "    ,! ,grt ,adv5ture",
            "",
            "  ,? is a simple test s5t;e = v;ifict5.",
            "",
            "  ,he wd v quick to run aft a l stormy ni<t.",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                                     #a"
        ]
    ]

    c = canvas.Canvas(dest_path, pagesize=letter)
    width, height = letter
    
    for page_lines in pages_text:
        c.setFont("Courier", 11)
        y = height - 54
        for line in page_lines:
            c.drawString(54, y, line)
            y -= 14
        c.showPage()
        
    c.save()
    print(f"[OK] Generated mock Braille PDF with errors: {os.path.abspath(dest_path)}")

def main():
    dest_dir = str(Path(__file__).resolve().parents[1] / "data/mock_files")
    os.makedirs(dest_dir, exist_ok=True)
    
    create_mock_docx(os.path.join(dest_dir, "english_sample.docx"))
    create_mock_braille_pdf(os.path.join(dest_dir, "braille_sample.pdf"))
    create_mismatch_braille_pdf(os.path.join(dest_dir, "braille_sample_errors.pdf"))
    
    print("\n" + "=" * 60)
    print("Files created inside the 'data/mock_files' directory.")
    print("For a 100% Correct Match:")
    print("  English: english_sample.docx")
    print("  Braille: braille_sample.pdf")
    print("\nFor Error/Mismatch testing:")
    print("  English: english_sample.docx")
    print("  Braille: braille_sample_errors.pdf")
    print("=" * 60)

if __name__ == "__main__":
    main()
