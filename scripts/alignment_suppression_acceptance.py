"""Reporting regressions; never mutates the clean fixture inputs."""
from pathlib import Path
from dataclasses import asdict
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from braille_app.validation.api import validate_document,adapt_validation_report
from braille_app.validation.validator import BrailleValidator
from braille_app.translation.expected_document import generate_expected_braille

def result(master,actual):
    return adapt_validation_report(BrailleValidator().validate(master,actual))

master={'pages':[{'print_page_number':1,'blocks':[
    {'text':'Alice checks [[*ts*]]26 + 13 = 39[[*te*]].'},
    {'text':'Robert records [[*ts*]]48 − 17 = 31[[*te*]].'},
    {'text':'The final observation is complete.'},
]}]}
blocks=generate_expected_braille(master).blocks
clean='⠀'.join(b.braille for b in blocks)
split=blocks[0].braille+'\f'+'⠀'.join(b.braille for b in blocks[1:])
assert not result(master,clean).errors
r=result(master,split)
assert not r.errors and not r.alignment_diagnostics
# A wrong operator before the page split must remain an error.
r=result(master,split.replace('⠬','⠤',1))
assert any(e.rule_id=='NEMETH_SIMPLE_LINEAR_001' for e in r.errors),r
# A missing initial capital on a correctly aligned first page must remain.
r=result(master,split[1:])
assert any(e.rule_id=='UEB_8' for e in r.errors),r
# Real truncation is not relocation; no other-page anchors exist.
r=result(master,blocks[0].braille)
assert not r.errors and not r.alignment_diagnostics
assert r.statistics['unresolved_math_spans'] == 1
# An unrelated extra page cannot turn a missing mathematical operator into a pass.
missing=clean.replace('⠬','',1)+'\f⠵⠵⠵⠵⠵'
r=result(master,missing)
assert not r.errors and r.statistics['unresolved_math_spans'] == 1
# Existing literal acceptance fixtures: all six math and three capital defects survive.
acceptance={}
for folder,cases in [('simple_math',[('correct',0),('corrupted',6)]),('basic_capitalization',[('clean',0),('corrupted',3)])]:
    base=ROOT/'data'/folder;m=json.loads((base/'master.json').read_text(encoding='utf8'))
    for name,count in cases:
        rr=validate_document(m,base/(name+'.pdf'))
        assert len(rr.errors)==count,(folder,name,rr)
        acceptance[f'{folder}/{name}']=rr.statistics
inventory=json.loads((ROOT/'stress_test/clean_audit_work/file_inventory.json').read_text())
fixtures=[]
for n,expected_suppressed in enumerate([0,0,0,0,0],1):
    base=ROOT/'stress_test'/f'Test_{n}'
    rr=validate_document(base/f'Synthetic_Test_{n:02}.pdf',base/f'Synthetic_Test_{n:02}_converted.pdf')
    assert not rr.errors and len(rr.alignment_diagnostics)==expected_suppressed,(n,rr.statistics)
    assert rr.statistics['math_spans_evaluated']==rr.statistics['math_spans_total']
    assert rr.statistics['capitalization_opportunities_evaluated']==rr.statistics['capitalization_opportunities_total']
    fixtures.append({'test':n,**asdict(rr)})
for group in inventory:
    for f in group['files']:
        assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
output={'status':'PASS','synthetic_checks':6,'acceptance':acceptance,'fixtures':fixtures,'input_files_unchanged':25,'limitation':'Known page-expansion and operator-spacing patterns are aligned as a continuous document stream. Unsupported constructs and unaligned spans remain outside certification.'}
(ROOT/'reports/alignment_suppression_acceptance.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','fixtures':[{'test':f['test'],'errors':len(f['errors']),'suppressed':len(f['alignment_diagnostics'])} for f in fixtures],'existing_acceptance':{k:v['errors'] for k,v in acceptance.items()},'input_files_unchanged':25}))

