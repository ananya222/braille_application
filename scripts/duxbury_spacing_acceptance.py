"""Test-only Duxbury spacing matrix with literal source/operator oracles."""
from pathlib import Path
from dataclasses import asdict
import sys,json,re,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from braille_app.validation.api import adapt_validation_report,validate_document
from braille_app.validation.validator import BrailleValidator
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.simple_math import parse,OperatorNode,RelationNode,NumberNode,expected
from braille_app.translation.braille_cells import cells_to_unicode
CASES=[('PLUS','26 + 13 = 39','⠬','⠤','2 + 3 + 4 = 9'),
 ('MINUS','20 − 8 = 12','⠤','⠬','12 − 3 − 4 = 5'),
 ('NEGATIVE','−2 + 5 = 3','⠤','⠬','−2 + 1 = −1'),
 ('MULTIPLY','4 × 3 = 12','⠈⠡','⠈⠌','2 × 3 × 4 = 24'),
 ('DIVIDE','8 ÷ 2 = 4','⠨⠌','⠨⠅','24 ÷ 3 ÷ 2 = 4'),
 ('EQUALS','x + y = z','⠨⠅','⠨⠌',None)]
OPS={'+':'⠬','−':'⠤','×':'⠈⠡','÷':'⠨⠌'}
DIG=dict(zip('0123456789','⠴⠂⠆⠒⠲⠢⠖⠶⠦⠔'))
LETTER=dict(zip('abcdefghijklmnopqrstuvwxyz','⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵'))
def noisy(expr,unary_gap=False):
    out=[]
    for node in parse(expr).nodes:
        if isinstance(node,NumberNode):out.append('⠼'+''.join(DIG[d] for d in node.text))
        elif isinstance(node,RelationNode):out.append('⠀⠨⠅⠀')
        elif isinstance(node,OperatorNode):out.append(OPS[node.text]+('⠀' if unary_gap else '') if node.unary else '⠀'+OPS[node.text]+'⠀')
        else:out.append(LETTER[node.text])
    return ''.join(out)
def master(expr,prefix='Alice checks ',suffix='.'):
    return {'pages':[{'print_page_number':1,'blocks':[{'text':prefix+'[[*ts*]]'+expr+'[[*te*]]'+suffix}]}]}
def actual_for(m,payloads):
    generated=generate_expected_braille(m);text=generated.pages[0].flatten();it=iter(payloads)
    return re.sub('⠸⠩⠀.*?⠀⠸⠱',lambda _m:'⠸⠩⠀'+next(it)+'⠀⠸⠱',text)
def mutate(raw,old,new,all_matches=False):
    # Replace whole semantic symbols; exclude the common prefix of two-cell operators.
    spans=[];out='';cursor=0
    for m in re.finditer(re.escape(old),raw):
        if not all_matches and spans:break
        out+=raw[cursor:m.start()];start=len(out);out+=new
        wrong=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
        spans.append((start+min(wrong),start+max(wrong)+1));cursor=m.end()
    out+=raw[cursor:];assert spans
    return out,spans
def matrix():
    variants=[]
    for feature,expr,old,new,repeated in CASES:
        for noise in [False,True]:
            for wrong in [False,True]:
                m=master(expr);raw=actual_for(m,[noisy(expr) if noise else expected(expr)]);locations=[]
                if wrong:raw,locations=mutate(raw,old,new)
                variants.append((f'{feature}/'+('noisy' if noise else 'clean')+'/'+('wrong' if wrong else 'correct'),m,raw,locations,'NEMETH_SIMPLE_LINEAR_001'))
        # Repeated equals uses two complete spans; equality twice inside one span is unsupported.
        m=master(repeated or expr)
        if repeated is None:m['pages'][0]['blocks'][0]['text']+=' Again [[*ts*]]x + y = z[[*te*]].'
        raw=actual_for(m,[noisy(repeated or expr)]*(1 if repeated else 2));raw,locations=mutate(raw,old,new,True)
        variants.append((feature+'/repeated/noisy_wrong',m,raw,locations,'NEMETH_SIMPLE_LINEAR_001'))
        m=master(expr,prefix='',suffix=' was checked.');raw=actual_for(m,[noisy(expr)]);raw,locations=mutate(raw,old,new)
        variants.append((feature+'/boundary/noisy_wrong',m,raw,locations,'NEMETH_SIMPLE_LINEAR_001'))
    for name,change in [('correct',None),('missing',''),('wrong','⠰'),('unnecessary','⠠')]:
        m=master('26 + 13 = 39',prefix='alice checks ' if name=='unnecessary' else 'Alice checks ')
        raw=actual_for(m,[noisy('26 + 13 = 39')]);loc=[]
        if name=='missing':raw=raw[1:];loc=[(0,1)]
        elif name=='wrong':raw='⠰'+raw[1:];loc=[(0,1)]
        elif name=='unnecessary':raw='⠠'+raw;loc=[(0,1)]
        variants.append(('CAPITAL/'+name+'/noisy_math',m,raw,loc,'UEB_8'))
    for wrong in (False,True):
        m=master('−26');raw=actual_for(m,[noisy('−26',True)]);loc=[]
        if wrong:raw,loc=mutate(raw,'⠤','⠬')
        variants.append(('NEGATIVE/unary_gap/'+('wrong' if wrong else 'correct'),m,raw,loc,'NEMETH_SIMPLE_LINEAR_001'))
    return variants
def run(phase):
    rows=[]
    for name,m,raw,locations,rule in matrix():
        result=adapt_validation_report(BrailleValidator().validate(m,raw))
        found=[(e.actual_cell_start,e.actual_cell_end) for e in result.errors]
        passed=len(result.errors)==len(locations) and set(found)==set(locations) and all(e.rule_id==rule for e in result.errors)
        rows.append({'case':name,'expected_errors':len(locations),'actual_errors':len(result.errors),'expected_actual_ranges':locations,'actual_ranges':found,'pass':passed,'raw_actual_braille':raw,'master':m,'result':asdict(result)})
    out={'phase':phase,'cases':len(rows),'passed':sum(x['pass'] for x in rows),'failed':[x['case'] for x in rows if not x['pass']],'production_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'src/braille_app/validation').glob('*.py')},'rows':rows,'repeated_equals':'One equality per span only; repeated equality tested in two separate spans.'}
    (R/f'reports/duxbury_spacing_{phase}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('rows','production_sha256')}))
    for x in rows:
        if not x['pass']:print(json.dumps({k:v for k,v in x.items() if k not in ('raw_actual_braille','master','result')}))
    return out
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'baseline')
