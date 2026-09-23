"""Every split position across supported math, preserving physical targets."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import CASES,master,noisy,actual_for
from braille_app.translation.simple_math import expected
from braille_app.validation.validator import BrailleValidator
from braille_app.validation.api import adapt_validation_report
rows=[]
def check(name,m,raw,cuts,targets):
    bounds=[0]+sorted(cuts)+[len(raw)]
    chunks=[raw[a:b] for a,b in zip(bounds,bounds[1:])]
    truth={(page+1,i-a) for page,(a,b) in enumerate(zip(bounds,bounds[1:])) for i in targets if a<=i<b}
    report=BrailleValidator().validate(m,'\f'.join(chunks));r=adapt_validation_report(report)
    found=set()
    for e in r.errors:
        ranges=e.localized_actual_ranges or ((e.actual_page_number,e.actual_cell_start,e.actual_cell_end),)
        for p,a,b in ranges:
            found.update((p,i) for i in range(a,b) if report.actual_pages[p-1][i])
    provenance=all(view.cells==tuple(report.actual_stream[i] for i in view.raw_indices) for view in report.comparison_views)
    ok=truth==found and r.statistics['math_spans_evaluated']==1 and provenance
    rows.append({'name':name,'cuts':cuts,'targets':sorted(truth),'found':sorted(found),'pass':ok,'statistics':r.statistics})

for family,source,old,new,_ in CASES:
    for spacing in (False,True):
        m=master(source,prefix='',suffix='');clean=actual_for(m,[noisy(source) if spacing else expected(source)])
        for wrong in (False,True):
            at=clean.index(old);raw=clean[:at]+new+clean[at+len(old):] if wrong else clean
            targets=[at+i for i,(a,b) in enumerate(zip(old,new)) if a!=b] if wrong else []
            for cut in range(1,len(raw)):
                check(f'{family}/spacing={spacing}/wrong={wrong}',m,raw,[cut],targets)
            # Split every nonblank pair, forcing several token joins at once.
            cuts=[i for i in range(1,len(raw)) if raw[i-1]!='⠀' and raw[i]!='⠀']
            check(f'{family}/many_pages/spacing={spacing}/wrong={wrong}',m,raw,cuts,targets)

# Both cells of a multiplication sign change, including a page between them.
source='123 × 2 = 246';m=master(source,prefix='',suffix='');raw=actual_for(m,[noisy(source)]);at=raw.index('⠈⠡')
raw=raw[:at]+'⠨⠌'+raw[at+2:]
check('two_changed_cells_on_two_pages',m,raw,[at+1],[at,at+1])
source='−25 + 30 = 5';m=master(source,prefix='',suffix='');raw=actual_for(m,['⠬'+noisy(source)[2:]])
for cut in range(1,len(raw)):check('leading_plus_no_numeric_indicator',m,raw,[cut],[3])

out={'cases':len(rows),'passed':sum(x['pass'] for x in rows),'failures':[x for x in rows if not x['pass']],'rows':rows}
(R/'reports/cross_page_acceptance.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ('rows','failures')}))
print('FAILURES',[(r['name'],r['cuts']) for r in out['failures']][:15])
assert not out['failures']
