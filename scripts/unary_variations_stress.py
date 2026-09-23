"""Test-only expansion of the observed leading-plus reconversion pattern."""
from pathlib import Path
import sys, json, re, hashlib, os, subprocess
from dataclasses import asdict
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from duxbury_spacing_acceptance import master, actual_for, noisy
from simple_math_acceptance import braille_pdf
from braille_app.translation.simple_math import expected
from braille_app.validation.api import validate_document, adapt_validation_report
from braille_app.validation.validator import BrailleValidator
from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance, validation_errors_to_legacy_cell_issues
from braille_app.validation.simple_math_comparison import _passages
from braille_app.visual_annotations import visual_issues_from_cell_issues, export_annotated_pdf
from pypdf import PdfReader, PdfWriter
import pdfplumber

OUT=ROOT/'output/unary_variations';OUT.mkdir(exist_ok=True)
numbers=(1,2,4,7,9,10,12,25,99,100,101,999)
rows=[];boundaries=[]
for n in numbers:
    sources=(f'−{n}',f'−{n} + {n+5} = 5',f'−{n} + {n} − {n} = −{n}',f'−{n} + x = x − {n}')
    for j,source in enumerate(sources):
        for spacing in (False,True):
            clean=noisy(source) if spacing else expected(source)
            for mode in ('clean','plus_with_indicator','plus_without_indicator'):
                payload=clean if mode=='clean' else '⠬'+clean[1 if mode=='plus_with_indicator' else 2:]
                m=master(source,prefix=('', 'Mira checks ', 'The result ', 'Here ')[j],suffix=('.', ' was checked.', '. Next we continue.', '.')[j])
                raw=actual_for(m,[payload]);r=adapt_validation_report(BrailleValidator().validate(m,raw))
                target=raw.index('⠸⠩')+3
                wanted=[] if mode=='clean' else [(target,target+1)]
                found=[(e.actual_cell_start,e.actual_cell_end) for e in r.errors]
                ok=found==wanted and r.statistics['math_spans_evaluated']==1
                rows.append({'source':source,'spacing':spacing,'mode':mode,'injected':len(wanted),'detected':len(set(found)&set(wanted)),'false_positives':len(set(found)-set(wanted)),'exact':found==wanted,'pass':ok})
    # Adjacent conditions are measured, not silently treated as supported.
    for location in ('leading_gap','after_equals'):
        source=f'−{n} + {n+5} = 5' if location=='leading_gap' else f'0 − {n} = −{n}'
        rawpayload=noisy(source)
        rawpayload=rawpayload.replace('⠤⠼','⠬⠀' if location=='leading_gap' else '⠬',1)
        m=master(source);raw=actual_for(m,[rawpayload]);r=adapt_validation_report(BrailleValidator().validate(m,raw))
        boundaries.append({'source':source,'variant':location,'errors':len(r.errors),'evaluated':r.statistics['math_spans_evaluated'],'unresolved':r.statistics['unresolved_math_spans']})

# Multiple spans share one paragraph. Some are clean and others are corrupted.
paragraphs=[]
for n in numbers:
    expressions=[f'−{n} + {n+2} = 2',f'−{n}',f'−{n} + {n} = 0']
    m={'pages':[{'print_page_number':1,'blocks':[{'text':'Nora checks '+'. Then '.join('[[*ts*]]'+s+'[[*te*]]' for s in expressions)+'.'}]}]}
    payloads=[noisy(s) for s in expressions]
    payloads[0]='⠬'+payloads[0][2:];payloads[2]='⠬'+payloads[2][2:]
    raw=actual_for(m,payloads)
    starts=[m.start()+3 for m in re.finditer('⠸⠩',raw)]
    wanted=[(starts[i],starts[i]+1) for i in (0,2)]
    r=adapt_validation_report(BrailleValidator().validate(m,raw))
    found=[(e.actual_cell_start,e.actual_cell_end) for e in r.errors]
    paragraphs.append({'number':n,'injected':2,'detected':len(set(found)&set(wanted)),'false_positives':len(set(found)-set(wanted)),'pass':found==wanted and r.statistics['math_spans_evaluated']==3})

# Three physical PDF pages, one logical source page; all 36 leading signs changed.
expressions=[s for n in numbers for s in (f'−{n}', f'−{n} + {n+5} = 5', f'−{n} + x = x − {n}')]
m={'pages':[{'print_page_number':1,'blocks':[{'text':'[[*ts*]]'+s+'[[*te*]]'} for s in expressions]}]}
(OUT/'master.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf8')
pdfresults=[]
for mode in ('clean','corrupted'):
    lines=['⠸⠩⠀'+(noisy(s) if mode=='clean' else '⠬'+noisy(s)[2:])+'⠀⠸⠱' for s in expressions]
    writer=PdfWriter()
    for i in range(3):
        page=OUT/f'{mode}_part_{i}.pdf';braille_pdf(page,lines[i*12:(i+1)*12]);writer.append(PdfReader(page))
    actual=OUT/f'{mode}.pdf'
    with actual.open('wb') as f:writer.write(f)
    _,prov=load_pdf_provenance(actual,profile='math')
    wanted=[]
    for page in prov.pages:
        for start,end in _passages(page.validator_cells)[0]:
            if mode=='corrupted':
                assert page.validator_cells[start+1]==44
                wanted.append((page.page,start+1,start+2))
    # Record targets before invoking the validator.
    (OUT/f'{mode}_targets.json').write_text(json.dumps(wanted),encoding='utf8')
    r=validate_document(m,actual)
    found=[(e.actual_page_number,e.actual_cell_start,e.actual_cell_end) for e in r.errors]
    assert found==wanted and r.statistics['math_spans_evaluated']==36,(mode,found)
    visual=visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(r,prov))
    annotated=OUT/f'{mode}_annotated.pdf';export_annotated_pdf(str(actual),str(annotated),visual)
    with pdfplumber.open(annotated) as pdf:
        blue=[(i,rect) for i,page in enumerate(pdf.pages,1) for rect in page.rects if isinstance(rect.get('stroking_color'),(tuple,list)) and len(rect['stroking_color'])==3 and all(abs(a-b)<.01 for a,b in zip(rect['stroking_color'],(.12,.48,1)))]
    assert len(blue)==len(wanted)
    for page,start,end in wanted:
        c=prov.cells_for_span(page,start,end)[0]
        assert sum(p==page and all(abs(rect[k]-getattr(c,k))<.015 for k in ('x0','top','x1','bottom')) for p,rect in blue)==1
    pdfresults.append({'mode':mode,'pages':3,'math_evaluated':36,'errors':len(found),'exact_physical_boxes':len(blue),'pass':True})

out={'basis':'Synthetic fixtures reproduce the observed uploaded Duxbury pattern. These are not new Duxbury conversions.',
     'matrix':rows,'paragraphs':paragraphs,'boundary_probes':boundaries,'pdf':pdfresults,
     'summary':{'matrix_cases':len(rows),'matrix_injected':sum(r['injected'] for r in rows),'matrix_detected':sum(r['detected'] for r in rows),'matrix_failures':sum(not r['pass'] for r in rows),'paragraph_injected':24,'paragraph_detected':sum(r['detected'] for r in paragraphs),'paragraph_failures':sum(not r['pass'] for r in paragraphs),'boundary_skipped':sum(not r['evaluated'] for r in boundaries),'boundary_cases':len(boundaries)}}
(OUT/'report.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(out['summary']))
assert all(r['pass'] for r in rows+paragraphs)
