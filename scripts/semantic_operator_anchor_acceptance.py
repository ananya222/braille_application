"""Repeated-operand paired substitutions must retain distinct raw targets."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import master,actual_for,noisy
from braille_app.translation.simple_math import expected
from braille_app.validation.api import adapt_validation_report
from braille_app.validation.validator import BrailleValidator
cases=[]
for source in ['m + n − n = m','m + 9 − 9 = m','x − y + y = x','31 + 8 − 8 = 31',
               'a + b − b + b − b = a','−7 + 9 − 9 = −7']:
    for spacing in [False,True]:
        m=master(source);a=actual_for(m,[noisy(source) if spacing else expected(source)])
        positions=[i for i,c in enumerate(a) if c in '⠬⠤']
        corrupted=''.join({'⠬':'⠤','⠤':'⠬'}.get(c,c) for c in a)
        raw=BrailleValidator().validate(m,corrupted);r=adapt_validation_report(raw)
        assert {(e.actual_cell_start,e.actual_cell_end) for e in r.errors}=={(p,p+1) for p in positions}
        assert len(r.errors)==len(positions) and all(e.rule_id=='NEMETH_SIMPLE_LINEAR_001' for e in r.errors)
        assert all(op.expected_end-op.expected_start==op.actual_end-op.actual_start for op in raw.page_alignments[0] if op.tag=='equal')
        cases.append({'source':source,'spacing':spacing,'errors':len(positions),'pass':True})
(R/'reports/semantic_operator_anchor_acceptance.json').write_text(json.dumps({'passed':len(cases),'cases':cases},indent=2),encoding='utf8')
print('Repeated-operand semantic alignment:',len(cases),'PASS')
