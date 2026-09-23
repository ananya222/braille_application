"""Capitalization acceptance using the existing Braille-dot PDF renderer."""
from pathlib import Path
import sys,json
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
DEST=ROOT/'data/basic_capitalization'
TEXTS=['Historical Note','Chapter One','historical note','A function is defined here.',
       'Let [[*ts*]]x = 3[[*te*]].','This is a Test.']
MASTER={'pages':[{'print_page_number':1,'blocks':[{'text':x} for x in TEXTS]}]}

def prepare():
    from braille_app.translation.expected_document import generate_expected_braille
    from braille_app.translation.braille_cells import BRF_DOTS,char_mask
    document=generate_expected_braille(MASTER)
    clean=[b.braille for b in document.blocks]
    assert clean[0][0]==clean[1][0]=='⠠' and clean[2][0]=='⠓'
    corrupted=list(clean)
    corrupted[0]=clean[0][1:]
    corrupted[1]='⠰'+clean[1][1:]
    corrupted[2]='⠠'+clean[2]
    offset=0; defects=[]
    for i,line in enumerate(corrupted):
        if i<3: defects.append({'kind':['missing','wrong','unnecessary'][i],'start':offset,'end':offset+1})
        offset+=len(line)+1
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'master.txt').write_text('\n'.join(TEXTS),encoding='utf8')
    (DEST/'master.json').write_text(json.dumps(MASTER,ensure_ascii=False,indent=2),encoding='utf8')
    (DEST/'fixture.json').write_text(json.dumps({'clean':clean,'corrupted':corrupted,'defects':defects},ensure_ascii=False,indent=2),encoding='utf8')
    reverse={char_mask(c,'duxbury'):c.upper() if c.isalpha() else c for c in BRF_DOTS}
    for name,lines in [('clean',clean),('corrupted',corrupted)]:
        (DEST/(name+'.brf')).write_text('\n'.join(''.join(reverse[ord(c)-0x2800] for c in line) for line in lines),encoding='ascii')

def build():
    from simple_math_acceptance import braille_pdf
    data=json.loads((DEST/'fixture.json').read_text(encoding='utf8'))
    for name in ['clean','corrupted']: braille_pdf(DEST/(name+'.pdf'),data[name])

def validate():
    from braille_app.validation.api import validate_document
    from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance,validation_errors_to_legacy_cell_issues
    from braille_app.visual_annotations import visual_issues_from_cell_issues,export_annotated_pdf
    data=json.loads((DEST/'fixture.json').read_text(encoding='utf8'))
    report={}
    for name,count in [('clean',0),('corrupted',3)]:
        pdf=DEST/(name+'.pdf')
        r=validate_document(MASTER,pdf)
        assert len(r.errors)==count and not r.reviews,(name,r)
        content,provenance=load_pdf_provenance(pdf,profile='math')
        assert not provenance.unmatched_cells and not provenance.unexplained_offsets
        visual=visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(r,provenance))
        assert len(visual)==count
        for e,d in zip(r.errors,data['defects']):
            assert e.rule_id=='UEB_8' and e.category=='UEB_ERROR' and d['kind'] in e.explanation
            assert (e.actual_cell_start,e.actual_cell_end)==(d['start'],d['end']),e
        if count:
            out=ROOT/'output/basic_capitalization';out.mkdir(parents=True,exist_ok=True)
            annotated=out/'corrupted_annotated.pdf'
            export_annotated_pdf(str(pdf),str(annotated),visual)
            content_after,_=load_pdf_provenance(annotated,profile='math')
            assert content_after.content==content.content
        report[name]={'statistics':r.statistics,'errors':[asdict(e) for e in r.errors],
                      'visual':[asdict(v) for v in visual],'unmatched':provenance.unmatched_cells,'offsets':provenance.unexplained_offsets}
    (ROOT/'reports/basic_capitalization_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print({k:v['statistics'] for k,v in report.items()})

if __name__=='__main__':
    if '--prepare' in sys.argv: prepare()
    if '--build' in sys.argv: build()
    if '--validate' in sys.argv: validate()
