"""Test-only PDF variants, reused unchanged before and after tolerance."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import matrix
from simple_math_acceptance import braille_pdf
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance,validation_errors_to_legacy_cell_issues
from braille_app.visual_annotations import visual_issues_from_cell_issues,export_annotated_pdf
D=R/'data/duxbury_spacing_tests';D.mkdir(exist_ok=True)
phase=sys.argv[1];rows=[]
for i,(name,m,raw,locations,rule) in enumerate(matrix(),1):
    pdf=D/f'case_{i:02}.pdf'
    if phase=='baseline':braille_pdf(pdf,[raw])
    before=hashlib.sha256(pdf.read_bytes()).hexdigest()
    r=validate_document(m,pdf);content,prov=load_pdf_provenance(pdf,profile='math')
    mapped=validation_errors_to_legacy_cell_issues(r,prov)
    visual=visual_issues_from_cell_issues(mapped)
    actualranges=[(e.actual_cell_start,e.actual_cell_end) for e in r.errors]
    passed=(len(r.errors)==len(locations) and set(actualranges)==set(locations) and all(e.rule_id==rule for e in r.errors) and not prov.unmatched_cells and not prov.unexplained_offsets)
    expected_boxes=[];found_boxes=[]
    for start,end in locations:expected_boxes.append([(c.page,c.x0,c.top,c.x1,c.bottom) for c in prov.cells_for_span(1,start,end)])
    for e in r.errors:found_boxes.append([(c.page,c.x0,c.top,c.x1,c.bottom) for c in prov.cells_for_span(1,e.actual_cell_start,e.actual_cell_end)])
    # Box equality explicitly verifies the wrong cell, not merely the page.
    passed=passed and expected_boxes==found_boxes
    if phase!='baseline':
        out=R/'output/duxbury_spacing_tests'/f'case_{i:02}_annotated.pdf';out.parent.mkdir(exist_ok=True)
        export_annotated_pdf(str(pdf),str(out),visual)
        after,_=load_pdf_provenance(out,profile='math');assert after.content==content.content
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()==before
    rows.append({'case':name,'pass':passed,'expected_errors':len(locations),'errors':len(r.errors),'expected_ranges':locations,'actual_ranges':actualranges,'expected_boxes':expected_boxes,'actual_boxes':found_boxes,'sha256':before,'input_pdf':str(pdf),'visual_count':len(visual),'provenance_unmatched':prov.unmatched_cells,'provenance_offsets':prov.unexplained_offsets})
report={'phase':phase,'cases':len(rows),'passed':sum(x['pass'] for x in rows),'failed':[x['case'] for x in rows if not x['pass']],'rows':rows}
(R/f'reports/duxbury_spacing_pdf_{phase}.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))

