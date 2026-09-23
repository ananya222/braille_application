"""DOCX regression: basic capitals in prose after and between marked math."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from duxbury_spacing_acceptance import noisy,actual_for
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator
from braille_app.validation.api import validate_document
from docx import Document
O=R/'output/docx_capital_fix';O.mkdir(exist_ok=True)
rows=[]
for layout in ('after','between','repeated','line_break'):
 for mode,word in [('clean','Nora'),('missing','Nora'),('wrong','Nora'),('extra','nora')]:
  for spacing in (False,True):
   for value in (7,25):
    expr=f'{value} + 5 = {value+5}'
    tail=word+' reads.'
    source='[[*ts*]]'+expr+'[[*te*]] '+tail
    if layout=='between':source+=' Then [[*ts*]]8 − 3 = 5[[*te*]].'
    if layout=='repeated':source='Nora reads. '+source+' Nora reads.'
    if layout=='line_break':source=source.replace('[[*te*]] ','[[*te*]]\n')
    m={'pages':[{'print_page_number':1,'blocks':[{'text':source}]}]}
    base=generate_expected_braille(m)
    payloads=[noisy(record.source) if spacing else record.braille for record in base.blocks[0].math_records]
    raw=actual_for(m,payloads)
    # Independent target: literal first prose word after the first terminator.
    word_cells=LiblouisTranslator().translate_prose(word)
    at=raw.index(word_cells,raw.index('⠸⠱')+2)
    if mode=='missing':raw=raw[:at]+raw[at+1:]
    elif mode=='wrong':raw=raw[:at]+'⠰'+raw[at+1:]
    elif mode=='extra':raw=raw[:at]+'⠠'+raw[at:]
    doc=Document();doc.add_paragraph(source);master=O/'case.docx';doc.save(master)
    r=validate_document(master,raw)
    wanted=[] if mode=='clean' else [(at,at+1)]
    found=[(e.actual_cell_start,e.actual_cell_end) for e in r.errors]
    assert found==wanted and all(e.rule_id=='UEB_8' for e in r.errors),(source,mode,found,wanted)
    rows.append({'layout':layout,'mode':mode,'spacing':spacing,'value':value,'pass':True})

# Unsupported preceding math must not grant a new capitalization guarantee.
for expr in ('2x + 1 = 3','1/2 + 1/2 = 1','2.5 + 1 = 3.5'):
 source='[[*ts*]]'+expr+'[[*te*]] Nora reads.'
 b=generate_expected_braille({'pages':[{'print_page_number':1,'blocks':[{'text':source}]}]}).blocks[0]
 assert not b.capital_sites
 rows.append({'guard':expr,'pass':True})
(O/'acceptance.json').write_text(json.dumps({'cases':len(rows),'passed':len(rows),'rows':rows},indent=2))
print(len(rows),'DOCX prose-capital cases PASS')
