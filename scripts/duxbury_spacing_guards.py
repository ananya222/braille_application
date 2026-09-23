"""Additional source/normalization guards and mixed-context regressions."""
from pathlib import Path
import sys,json,difflib,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import CASES,master,noisy,actual_for
from braille_app.translation.simple_math import expected
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.validator import BrailleValidator
from braille_app.validation.api import adapt_validation_report
from braille_app.translation.braille_cells import unicode_to_cells
rows=[]
def check(name,m,raw):
    report=BrailleValidator().validate(m,raw);result=adapt_validation_report(report)
    for view,actual in zip(report.comparison_views,report.actual_pages):
        assert view.cells==tuple(actual[i] for i in view.raw_indices)
        assert list(view.raw_indices)==sorted(set(view.raw_indices))
    for pg,ops,actual in zip(report.expected_document.pages,report.page_alignments,report.actual_pages):
        exp=unicode_to_cells(pg.flatten())
        for op in ops:
            if op.tag=='equal':assert exp[op.expected_start:op.expected_end]==actual[op.actual_start:op.actual_end]
    rows.append({'case':name,'errors':len(result.errors),'normalized_spans':result.statistics['duxbury_normalized_spans']})
    return report,result
symbols=['⠬','⠤','⠈⠡','⠨⠌','⠨⠅']
for feature,expr,old,_wrong,_repeat in CASES:
    for noise in (False,True):
        for new in symbols:
            if old==new:continue
            m=master(expr);raw=actual_for(m,[noisy(expr) if noise else expected(expr)])
            start=raw.index(old);raw=raw[:start]+new+raw[start+len(old):]
            report,result=check(f'{feature}/swap/{symbols.index(new)}/noise={noise}',m,raw)
            assert result.errors,(feature,new)
            assert all(e.rule_id=='NEMETH_SIMPLE_LINEAR_001' for e in result.errors)
            expected_wrong=set()
            for tag,i,j,k,l in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
                if tag!='equal':expected_wrong.update(range(start+k,start+l))
            actual_wrong=set(i for e in result.errors for i in range(e.actual_cell_start,e.actual_cell_end))
            assert expected_wrong==actual_wrong,(feature,new,expected_wrong,actual_wrong)
# Corrupt the first component, not just the last, of multi-cell operators.
for feature,expr,old,_new,_repeat in CASES:
    if len(old)!=2:continue
    m=master(expr);raw=actual_for(m,[noisy(expr)]);pos=raw.index(old);raw=raw[:pos]+'⠐'+raw[pos+1:]
    _,result=check(feature+'/wrong_prefix/noisy',m,raw)
    assert [(e.actual_cell_start,e.actual_cell_end) for e in result.errors]==[(pos,pos+1)]
# A capital in a following paragraph must retain its original raw PDF index.
for kind in ('correct','missing','wrong','unnecessary'):
    m=master('26 + 13 = 39');m['pages'][0]['blocks'].append({'text':'alice checks.' if kind=='unnecessary' else 'Alice checks.'})
    raw=actual_for(m,[noisy('26 + 13 = 39')]);last=raw.rfind('⠀') # use the independently generated last block for exact boundary
    tail=generate_expected_braille(m).blocks[-1].braille;pos=len(raw)-len(tail)
    if kind=='missing':raw=raw[:pos]+raw[pos+1:]
    if kind=='wrong':raw=raw[:pos]+'⠰'+raw[pos+1:]
    if kind=='unnecessary':raw=raw[:pos]+'⠠'+raw[pos:]
    _,result=check('CAPITAL/following_paragraph/'+kind,m,raw)
    assert len(result.errors)==int(kind!='correct')
    if result.errors:assert result.errors[0].rule_id=='UEB_8' and result.errors[0].actual_cell_start==pos
# Unsupported/non-observed edits must remain in the raw comparison.
m=master('26 + 13 = 39');normal=actual_for(m,[noisy('26 + 13 = 39')])
variants={
 'two_blanks':normal.replace('⠀⠬⠀','⠀⠀⠬⠀'),
 'blank_inside_number':normal.replace('⠼⠆⠖','⠼⠆⠀⠖'),
 'changed_operand':normal.replace('⠼⠆⠖','⠼⠆⠶'),
 'missing_equals_blank':normal.replace('⠀⠨⠅⠀','⠨⠅⠀'),
 'doubled_equals_blank':normal.replace('⠀⠨⠅⠀','⠀⠀⠨⠅⠀'),
 'extra_numeric_without_gap':actual_for(m,[expected('26 + 13 = 39')]).replace('⠬','⠬⠼'),
 'missing_switch_blank':normal.replace('⠸⠩⠀','⠸⠩'),
 'extra_terminator':normal.replace('⠸⠩⠀','⠸⠩⠀⠸⠱'),
}
for name,raw in variants.items():
    report,_=check('GUARD/'+name,m,raw)
    assert report.comparison_views[0].cells==report.actual_pages[0],name
# Long repeated supported source stays eligible; no arbitrary length cutoff.
expr=' + '.join(['1']*150)+' = 150';m=master(expr);raw=actual_for(m,[noisy(expr)])
report,result=check('long_supported_chain',m,raw);assert not result.errors and report.comparison_views[0].normalized_spans
# Source outside the closed grammar is not granted tolerance.
for expr in ('2.5 + 1 = 3.5','x = y = z','2 / 3'):
    m=master(expr);raw=generate_expected_braille(m).pages[0].flatten()
    report,_=check('GUARD/unsupported_source/'+expr,m,raw)
    assert not report.comparison_views[0].normalized_spans
# Same canonical math but prose outside spans must stay byte-for-cell intact.
m=master('26 + 13 = 39',suffix=' Some prose remains.');raw=actual_for(m,[noisy('26 + 13 = 39')])
report,result=check('prose_preserved',m,raw);view=report.comparison_views[0]
assert ''.join(chr(0x2800+c) for c in view.cells)==generate_expected_braille(m).pages[0].flatten()
baseline=json.loads((R/'reports/duxbury_spacing_pdf_baseline.json').read_text())
for row in baseline['rows']:assert hashlib.sha256(Path(row['input_pdf']).read_bytes()).hexdigest()==row['sha256']
out={'status':'PASS','cases':len(rows),'rows':rows,'all_42_test_pdf_hashes_unchanged':True,'mapping_checks':'Every projected equal opcode equals its raw actual slice; canonical cells match their raw-index map.'}
(R/'reports/duxbury_spacing_guards.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
