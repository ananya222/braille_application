"""Physical page-boundary probes using unchanged production EXE."""
from pathlib import Path
import sys,json,os,subprocess
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from simple_math_acceptance import braille_pdf
from duxbury_spacing_acceptance import master,actual_for,noisy
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance,validation_errors_to_legacy_cell_issues
from braille_app.visual_annotations import visual_issues_from_cell_issues,export_annotated_pdf
from pypdf import PdfReader,PdfWriter
from docx import Document
import pdfplumber
O=R/'output/release_adversarial/pdf';O.mkdir(exist_ok=True)
rows=[]
def test(name,text,raw,target,split):
 folder=O/name;folder.mkdir(exist_ok=True)
 m={'pages':[{'print_page_number':1,'blocks':[{'text':text}]}]}
 doc=Document();doc.add_paragraph(text);doc.save(folder/'master.docx')
 chunks=[raw] if split is None else [raw[:split],raw[split:]]
 writer=PdfWriter()
 for i,chunk in enumerate(chunks):
  p=folder/f'part{i}.pdf';braille_pdf(p,[chunk]);writer.append(PdfReader(p))
 actual=folder/'actual.pdf'
 with actual.open('wb') as f:writer.write(f)
 _,prov=load_pdf_provenance(actual,profile='math')
 # Locate the injected glyph by its known position in the drawn chunk.
 pg=1 if split is None or target<split else 2
 local=target if pg==1 else target-split
 rank=sum(c!='⠀' for c in chunks[pg-1][:local])
 c=prov.pages[pg-1].provenance_cells[rank]
 truth={'page':pg,'rectangle':{k:getattr(c,k) for k in ('x0','top','x1','bottom')},'chunk_offset':local}
 (folder/'truth.json').write_text(json.dumps(truth),encoding='utf8')
 result=validate_document(m,actual)
 visual=visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(result,prov))
 dest=folder/'annotated.pdf';export_annotated_pdf(str(actual),str(dest),visual)
 with pdfplumber.open(dest) as pdf:
  boxes=[(i,b) for i,page in enumerate(pdf.pages,1) for b in page.rects if isinstance(b.get('stroking_color'),(tuple,list)) and len(b['stroking_color'])==3 and all(abs(a-v)<.01 for a,v in zip(b['stroking_color'],(.12,.48,1)))]
 exact=sum(p==pg and all(abs(b[k]-v)<.015 for k,v in truth['rectangle'].items()) for p,b in boxes)
 rows.append({'name':name,'errors':len(result.errors),'exact_target':exact==1,'other_boxes':len(boxes)-exact,'statistics':result.statistics,'truth':truth,'pass':exact==1 and len(boxes)==1})

source='123 × 2 = 246';text='[[*ts*]]'+source+'[[*te*]]';raw='⠸⠩⠀'+noisy(source)+'⠀⠸⠱'
at=raw.index('⠈⠡')+1;raw=raw[:at]+'⠌'+raw[at+1:]
for name,split in [('multiply_unsplit',None),('between_operator_cells',at),('inside_operand',raw.index('⠼')+2),('inside_open_switch',1),('inside_close_switch',len(raw)-1),('before_operator',at-1),('after_operator',at+1)]:
 test(name,text,raw,at,split)
source='−25 + 30 = 5';text='[[*ts*]]'+source+'[[*te*]]';raw='⠸⠩⠀⠬'+noisy(source)[2:]+'⠀⠸⠱'
test('after_leading_plus',text,raw,3,4)
# Capital substitution and missing-indicator anchor at a physical page boundary.
from braille_app.translation.expected_document import generate_expected_braille
text='Alice reads.';m={'pages':[{'print_page_number':1,'blocks':[{'text':text}]}]};raw=generate_expected_braille(m).pages[0].flatten()
test('capital_indicator_split',text,'⠰'+raw[1:],0,1)
test('capital_missing',text,raw[1:],0,None)
for family,source,old,new in [('plus','7 + 5 = 12','⠬','⠤'),('minus','18 − 6 = 12','⠤','⠬'),('divide','28 ÷ 4 = 7','⠌','⠅'),('equals','x + y = z','⠅','⠌')]:
 text='[[*ts*]]'+source+'[[*te*]]';raw='⠸⠩⠀'+noisy(source)+'⠀⠸⠱';at=raw.index(old)
 test(family+'_control',text,raw[:at]+new+raw[at+1:],at,None)

# Reproduce all physical probes through the existing packaged worker.
exe=R/'dist/unary_fix_release/BrailleValidator/BrailleValidator.exe'
env=os.environ.copy();env.update(QT_QPA_PLATFORM='offscreen',LOCALAPPDATA=str(O/'runtime'))
for row in rows:
 f=O/row['name'];dest=f/'exe.json'
 env['LOCALAPPDATA']=str(f/'runtime')
 p=subprocess.run([str(exe),'--packaging-smoke','--master',str(f/'master.docx'),'--braille',str(f/'actual.pdf'),'--result',str(dest)],env=env,capture_output=True,timeout=120)
 d=json.loads(dest.read_text(encoding='utf8'))
 row['exe_errors']=d['statistics']['errors'] if d['statistics'] else None
 row['exe_ok']=p.returncode==0 and not d['error'] and not d['annotation_error']
 row['exe_matches']=row['exe_errors']==row['errors'] and row['exe_ok']
 print(row['name'],row['errors'],row['pass'],'EXE',row['exe_matches'],flush=True)
(O/'report.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
