"""Reproducible public-scope fixture. Oracles are literal standards applications.

Run `--build` with artifact Python; `--validate` with the project runtime.
No Duxbury stream or generated candidate is used to construct correct cells.
"""
from pathlib import Path
import sys, json, io, re
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
DEST = ROOT / 'data/simple_math'
CASES = [
    ('Addition', '2 + 3 = 5', '⠼⠆⠬⠒⠀⠨⠅⠀⠼⠢', '⠬', '⠤'),
    ('Subtraction', '8 − 3 = 5', '⠼⠦⠤⠒⠀⠨⠅⠀⠼⠢', '⠤', '⠬'),
    ('Negative', '−2 + 5 = 3', '⠤⠼⠆⠬⠢⠀⠨⠅⠀⠼⠒', '⠤', '⠬'),
    ('Multiplication', '4 × 3 = 12', '⠼⠲⠈⠡⠒⠀⠨⠅⠀⠼⠂⠆', '⠡', '⠌'),
    ('Division', '8 ÷ 2 = 4', '⠼⠦⠨⠌⠆⠀⠨⠅⠀⠼⠲', '⠌', '⠅'),
    ('Equality', 'x + y = z', '⠭⠬⠽⠀⠨⠅⠀⠵', '⠅', '⠌'),
    ('Letter subtraction', 'x − y = z', '⠭⠤⠽⠀⠨⠅⠀⠵', None, None),
]


def master():
    return {'pages': [{'print_page_number': 1, 'blocks': [
        {'text': '[[*ts*]]' + source + '[[*te*]]'} for _,source,*_ in CASES]}]}


def lines(corrupt=False):
    return ['⠸⠩⠀' + (cells.replace(old,new,1) if corrupt and old else cells) + '⠀⠸⠱'
            for _,_,cells,old,new in CASES]


def braille_pdf(path, rows):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject
    from braille_app.translation.braille_cells import BRF_DOTS, char_mask
    pdfmetrics.registerFont(TTFont('Braille', 'C:/Windows/Fonts/seguisym.ttf'))
    buffer=io.BytesIO(); c=canvas.Canvas(buffer, pagesize=(612,792))
    c.setFont('Braille',16)
    for i,row in enumerate(rows): c.drawString(48,730-i*42,row)
    c.save()
    # Reuse the established demo font-map technique: dots visually, NABCC
    # extraction for the existing PDF reader. Not a new annotation engine.
    reader=PdfReader(io.BytesIO(buffer.getvalue()))
    canonical={char_mask(ch,'duxbury'):ch.upper() if ch.isalpha() else ch for ch in BRF_DOTS}
    for page in reader.pages:
        for ref in page['/Resources']['/Font'].values():
            font=ref.get_object()
            if '/ToUnicode' not in font: continue
            original=font['/ToUnicode'].get_object().get_data().decode('ascii')
            def remap(m):
                cp=int(m[2],16)
                return m[1]+'<%04X>'%ord(canonical[cp-0x2800]) if 0x2800<=cp<0x2840 else m[0]
            stream=DecodedStreamObject()
            stream.set_data(re.sub(r'(<[0-9A-Fa-f]+>\s*)<([0-9A-Fa-f]{4})>',remap,original).encode('ascii'))
            font[NameObject('/ToUnicode')]=stream
    writer=PdfWriter(); writer.append(reader)
    with path.open('wb') as output: writer.write(output)


def build():
    from braille_app.translation.braille_cells import BRF_DOTS, char_mask
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'master.json').write_text(json.dumps(master(),indent=2,ensure_ascii=False),encoding='utf8')
    (DEST/'master.txt').write_text('\n'.join(b['text'] for b in master()['pages'][0]['blocks']),encoding='utf8')
    reverse={char_mask(ch,'duxbury'):ch.upper() if ch.isalpha() else ch for ch in BRF_DOTS}
    for name,corrupt in [('correct',False),('corrupted',True)]:
        rows=lines(corrupt)
        (DEST/(name+'.brf')).write_text('\n'.join(''.join(reverse[ord(c)-0x2800] for c in row) for row in rows),encoding='ascii')
        braille_pdf(DEST/(name+'.pdf'),rows)


def validate():
    from dataclasses import asdict
    from braille_app.validation.api import validate_document
    from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance, validation_errors_to_legacy_cell_issues
    from braille_app.visual_annotations import visual_issues_from_cell_issues, export_annotated_pdf
    report={}
    for name,count in [('correct',0),('corrupted',6)]:
        path=DEST/(name+'.pdf')
        result=validate_document(master(),path)
        assert len(result.errors)==count and not result.reviews, result
        pdf,provenance=load_pdf_provenance(path,profile='math')
        assert not provenance.unmatched_cells and not provenance.unexplained_offsets
        visual=visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(result,provenance))
        assert len(visual)==count, visual
        for issue in result.errors:
            assert issue.rule_id=='NEMETH_SIMPLE_LINEAR_001' and issue.category=='NEMETH_ERROR'
            assert issue.actual_cell_end-issue.actual_cell_start==1
        out=ROOT/'output/simple_math'; out.mkdir(parents=True,exist_ok=True)
        destination=out/(name+'_annotated.pdf')
        export_annotated_pdf(str(path),str(destination),visual)
        after,_=load_pdf_provenance(destination,profile='math')
        assert after.content==pdf.content
        report[name]={'statistics':result.statistics,'errors':[asdict(x) for x in result.errors],
                      'visual':[asdict(x) for x in visual], 'unmatched':provenance.unmatched_cells,
                      'offsets':provenance.unexplained_offsets}
    (ROOT/'reports/simple_math_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v['statistics'] for k,v in report.items()}))


if __name__=='__main__':
    if '--build' in sys.argv: build()
    if '--validate' in sys.argv: validate()
