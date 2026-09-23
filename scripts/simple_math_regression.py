"""Read-only Chapter 1 regression; fixtures never influence rule behavior."""
import sys,json,runpy
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from braille_app.validation.api import validate_document,_docx_paragraph_dict
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation import math_translator

source=ROOT/'data/chapter1/chapter1_duxbury_ready_minus_fixed.docx'
master=_docx_paragraph_dict(source)
after=generate_expected_braille(master)
original=math_translator.simple_expected
try:
    math_translator.simple_expected=lambda _:None
    before=generate_expected_braille(master)
finally:
    math_translator.simple_expected=original
changes=[]
for old,new in zip(before.blocks,after.blocks):
    if old.braille!=new.braille:
        assert len(old.math_records)==len(new.math_records)
        for a,b in zip(old.math_records,new.math_records):
            if a.braille!=b.braille:
                assert original(b.source)==b.braille
                changes.append({'page':new.source_page,'source':b.source,'before':a.braille,'after':b.braille,
                                'rule':'NEMETH_SIMPLE_LINEAR_001'})
results={}
for name,path in [('clean','data/chapter1/chapter1_duxbury_ready_minus_fixed.brf'),
                  ('corrupted','data/chapter1/demo_evidence/Chapter1_Corrupted_Demo.brf')]:
    result=validate_document(source,ROOT/path)
    results[name]={'statistics':result.statistics,'errors':[asdict(e) for e in result.errors]}
cells=after.flatten()
results['switching']={'enter':cells.count('⠸⠩'),'exit':cells.count('⠸⠱'),
    'missing_inner_spaces':sum(cells[i+2:i+3]!='⠀' for i in range(len(cells)) if cells[i:i+2]=='⠸⠩')+
                          sum(cells[i-1:i]!='⠀' for i in range(len(cells)) if cells[i:i+2]=='⠸⠱')}
results['generator_changes']=changes
results['focused_tests']={}
for name in ['test_translation_tabs.py','test_prose_boundary_context.py','test_nemeth_boundary_spacing.py',
             'test_boundary_verifier.py','test_letter_grouping.py']:
    try:
        runpy.run_path(str(ROOT/'tests'/name),run_name='__main__')
        results['focused_tests'][name]='PASS'
    except Exception as exc:
        results['focused_tests'][name]=repr(exc)
(ROOT/'reports/simple_math_regression.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in results.items() if k not in ['generator_changes','clean','corrupted']}))
print('CLEAN',results['clean']['statistics'],'CORRUPTED',results['corrupted']['statistics'])
print('Changed math payloads',len(changes))
