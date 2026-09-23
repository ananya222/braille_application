"""Adversarial test fixtures only. Never changes production code or originals."""
from pathlib import Path
import sys,json,hashlib,re,collections
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import master,actual_for,noisy
from braille_app.translation.simple_math import expected
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.validator import BrailleValidator
from braille_app.validation.api import adapt_validation_report
O=R/'output/release_adversarial';O.mkdir(exist_ok=True)
rows=[];fixtures=[]

def apply(raw,edits):
    out='';cursor=0;targets=[]
    for start,end,new,family in sorted(edits):
        assert start>=cursor
        out+=raw[cursor:start];pos=len(out);old=raw[start:end]
        # Physical substitution targets exclude unchanged prefix/suffix cells.
        left=0
        while left<min(len(old),len(new)) and old[left]==new[left]:left+=1
        right=0
        while right<min(len(old)-left,len(new)-left) and old[-1-right]==new[-1-right]:right+=1
        indices=list(range(pos+left,pos+len(new)-right))
        if not indices:indices=[pos] # documented next-cell anchor for deletion
        targets.append({'family':family,'indices':indices,'kind':'deletion_anchor' if not new else 'replacement' if old else 'extra'})
        out+=new;cursor=end
    return out+raw[cursor:],targets

def run(name,m,raw,targets=(),tier='supported'):
    try:
        rep=BrailleValidator().validate(m,raw);r=adapt_validation_report(rep)
        found=[{'rule':e.rule_id,'indices':list(range(e.actual_cell_start,e.actual_cell_end)),'source':e.source_text} for e in r.errors]
        used=set();detected=0;exact=0
        for t in targets:
            rule='UEB_8' if t['family']=='CAPITALIZATION' else 'NEMETH_SIMPLE_LINEAR_001'
            hits=[i for i,e in enumerate(found) if e['rule']==rule and set(e['indices'])&set(t['indices'])]
            detected+=bool(hits);used.update(hits)
            exact+=any(found[i]['indices']==t['indices'] for i in hits)
        invariant=True
        for view,actual in zip(rep.comparison_views,rep.actual_pages):
            invariant &= view.cells==tuple(actual[i] for i in view.raw_indices)
        row={'name':name,'tier':tier,'targets':targets,'injected':len(targets),'detected':detected,'exact_raw':exact,'missed':len(targets)-detected,'unmatched_reports':len(found)-len(used),'statistics':r.statistics,'reported':found,'provenance_invariant':invariant,'pass':detected==len(targets) and exact==len(targets) and len(found)==len(used) and invariant}
        if not targets:row['pass'] &= r.statistics['unresolved_math_spans']==0
    except Exception as e:row={'name':name,'tier':tier,'targets':targets,'injected':len(targets),'pass':False,'exception':repr(e)}
    rows.append(row)
    if not row['pass']:fixtures.append({'name':name,'master':m,'raw':raw,'targets':targets})
    return row

symbols=['⠬','⠤','⠈⠡','⠨⠌','⠨⠅']
families={
 'PLUS':('⠬',['0 + 0 = 0','99 + 1 = 100','x + y = z','1 + 1 + 1 = 3','12 + 12 − 12 = 12','−7 + 9 = 2']),
 'MINUS':('⠤',['0 − 0 = 0','100 − 99 = 1','x − y = z','9 − 3 − 3 = 3','12 − 12 + 12 = 12','7 − 9 = −2']),
 'NEGATIVE':('⠤',['−1','−999 + 1000 = 1','−7 + x = x − 7','−2 + 1 = −1','0 − 12 = −12','−100 + 100 = 0']),
 'MULTIPLY':('⠈⠡',['0 × 9 = 0','99 × 10 = 990','x × y = z','2 × 2 × 2 = 8','3 × 4 + 3 × 4 = 24','−2 × 3 = −6']),
 'DIVIDE':('⠨⠌',['0 ÷ 9 = 0','1000 ÷ 10 = 100','x ÷ y = z','24 ÷ 2 ÷ 2 = 6','12 ÷ 3 + 12 ÷ 3 = 8','−12 ÷ 3 = −4']),
 'EQUALS':('⠨⠅',['0 = 0','1000 = 1000','x = y','1 + 1 + 1 = 3','−12 = −12','3 × 4 = 24 ÷ 2'])}
for family,(old,sources) in families.items():
 for source in sources:
  for spacing in (False,True):
   m=master(source);raw=actual_for(m,[noisy(source) if spacing else expected(source)])
   label=f'{family}/{source}/spacing={spacing}'
   run(label+'/clean',m,raw)
   locations=[x.start() for x in re.finditer(re.escape(old),raw)]
   if family=='MINUS':locations=locations[:1]
   if family=='NEGATIVE':locations=[locations[-1] if source.startswith('0 ') else locations[0]]
   for new in symbols:
    if new==old:continue
    for mode in ('first','all') if len(locations)>1 else ('first',):
     edits=[(i,i+len(old),new,family) for i in (locations if mode=='all' else locations[:1])]
     changed,truth=apply(raw,edits);run(label+f'/{new}/{mode}',m,changed,truth)
   if len(old)==2:
    for cell in (0,1):
     i=locations[0]+cell;changed,truth=apply(raw,[(i,i+1,'⠐',family)])
     run(label+f'/component_{cell}',m,changed,truth)

# Dense repeated chains: all operators wrong, operands identical.
for family,op,old,new,source in (
 ('PLUS','+', '⠬','⠤',' + '.join(['1']*80)+' = 80'),
 ('MINUS','−','⠤','⠬','100'+' − 1'*80+' = 20'),
 ('MULTIPLY','×','⠈⠡','⠨⠌',' × '.join(['1']*40)+' = 1'),
 ('DIVIDE','÷','⠨⠌','⠈⠡','1'+' ÷ 1'*40+' = 1')):
 for spacing in (False,True):
  m=master(source);raw=actual_for(m,[noisy(source) if spacing else expected(source)])
  changed,truth=apply(raw,[(i.start(),i.end(),new,family) for i in re.finditer(re.escape(old),raw)])
  run(f'long_chain/{family}/{spacing}',m,changed,truth)

texts=['Alice reads.','Robert writes.','A child reads.','I can read.','O dear.','Alice Alice Alice.','The Cat Sat.','Historical Note','Alice reads. Robert writes.','Alice checks [[*ts*]]12 + 8 = 20[[*te*]].','Alice, Robert and Nora read.']
for text in texts:
 m={'pages':[{'print_page_number':1,'blocks':[{'text':text}]}]}
 raw=generate_expected_braille(m).pages[0].flatten();run('CAPITAL/clean/'+text,m,raw)
 positions=[x.start() for x in re.finditer('⠠',raw)]
 for mode,new in [('missing',''),('wrong','⠰')]:
  for which in ('first','all'):
   chosen=positions[:1] if which=='first' else positions
   changed,truth=apply(raw,[(i,i+1,new,'CAPITALIZATION') for i in chosen])
   run(f'CAPITAL/{mode}/{which}/{text}',m,changed,truth)
for text in ['alice reads.','the cat sat.','historical note','alice alice alice.']:
 m={'pages':[{'print_page_number':1,'blocks':[{'text':text}]}]};doc=generate_expected_braille(m);raw=doc.pages[0].flatten()
 sites=[s.expected_start for s in doc.blocks[0].capital_sites if not s.uppercase]
 for mode in ('first','all'):
  changed,truth=apply(raw,[(i,i,'⠠','CAPITALIZATION') for i in (sites[:1] if mode=='first' else sites)])
  run('CAPITAL/extra/'+mode+'/'+text,m,changed,truth)

# Simultaneous capital deletion, unequal-width math swaps and later capital errors.
for repeats in (2,5,12):
 blocks=[{'text':'Alice checks [[*ts*]]3 × 4 + 2 = 14[[*te*]].'},{'text':'Robert reads.'}]*repeats
 m={'pages':[{'print_page_number':1,'blocks':blocks}]};raw=generate_expected_braille(m).pages[0].flatten()
 edits=[(i.start(),i.end(),'','CAPITALIZATION') for i in re.finditer('⠠',raw)]
 edits += [(i.start(),i.end(),'⠤','MULTIPLY') for i in re.finditer('⠈⠡',raw)]
 edits += [(i.start(),i.end(),'⠨⠌','PLUS') for i in re.finditer('⠬',raw)]
 changed,truth=apply(raw,edits);run(f'combined/{repeats}',m,changed,truth)

# Out-of-guarantee probes measure whether damage disables later supported spans.
for kind in ('double_blank','missing_open','missing_close','extra_close','operand_changed'):
 sources=['7 + 5 = 12','8 − 3 = 5','4 × 3 = 12']
 m={'pages':[{'print_page_number':1,'blocks':[{'text':'[[*ts*]]'+s+'[[*te*]]'} for s in sources]}]}
 raw=actual_for(m,[noisy(s) for s in sources])
 if kind=='double_blank':raw=raw.replace('⠀⠬⠀','⠀⠀⠬⠀',1)
 if kind=='missing_open':raw=raw.replace('⠸⠩','',1)
 if kind=='missing_close':raw=raw.replace('⠸⠱','',1)
 if kind=='extra_close':raw=raw.replace('⠸⠱','⠸⠱⠀⠸⠱',1)
 if kind=='operand_changed':raw=raw.replace('⠼⠶','⠼⠦',1)
 i=raw.index('⠈⠡');changed,truth=apply(raw,[(i,i+2,'⠨⠌','MULTIPLY')])
 run('boundary/'+kind,m,changed,truth,tier='boundary_recovery')

for family,(old,sources) in families.items():
 source=sources[0];m=master(source);raw=actual_for(m,[noisy(source)]);at=raw.index(old)
 for mode,new in [('missing_operator',''),('duplicated_operator',old+old)]:
  changed,truth=apply(raw,[(at,at+len(old),new,family)])
  run(f'nonstandard_edit/{family}/{mode}',m,changed,truth,tier='beyond_verified_corruption_shapes')
 # The correct source is supported, but two adjacent blanks are not verified.
 new='⠤' if old!='⠤' else '⠬'
 changed,truth=apply(raw,[(at,at+len(old),new,family)])
 changed=changed[:at]+'⠀⠀'+changed[at:]
 for t in truth:t['indices']=[i+2 for i in t['indices']]
 run(f'nonstandard_spacing/{family}',m,changed,truth,tier='beyond_verified_corruption_shapes')

for text in ['NASA reads.','iPhone works.','Alice has 2 books.','[[*ts*]]2 + 3 = 5[[*te*]] Alice reads.']:
 m={'pages':[{'print_page_number':1,'blocks':[{'text':text}]}]};raw=generate_expected_braille(m).pages[0].flatten()
 if '⠠' in raw:
  i=raw.index('⠠');changed,truth=apply(raw,[(i,i+1,'⠰','CAPITALIZATION')]);run('scope/'+text,m,changed,truth,tier='outside_guarantee')

summary={}
for tier in sorted({r['tier'] for r in rows}):
 selected=[r for r in rows if r['tier']==tier]
 summary[tier]={'cases':len(selected),'failed_cases':sum(not r['pass'] for r in selected),'injected':sum(r['injected'] for r in selected),'detected':sum(r.get('detected',0) for r in selected),'exact_raw':sum(r.get('exact_raw',0) for r in selected),'missed':sum(r.get('missed',0) for r in selected),'unmatched_reports':sum(r.get('unmatched_reports',0) for r in selected),'exceptions':sum('exception' in r for r in selected)}
(O/'matrix.json').write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=2),encoding='utf8')
(O/'failure_fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
