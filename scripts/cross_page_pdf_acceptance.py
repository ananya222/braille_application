"""Physical and frozen-EXE checks for page-spanning math errors."""
from pathlib import Path
import sys,json,os,subprocess,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import load_pdf_provenance,validation_errors_to_legacy_cell_issues
from braille_app.visual_annotations import visual_issues_from_cell_issues,export_annotated_pdf
from simple_math_acceptance import braille_pdf
from duxbury_spacing_acceptance import noisy
from pypdf import PdfReader,PdfWriter
from docx import Document
import pdfplumber
O=R/'output/cross_page_fix';O.mkdir(exist_ok=True)
prior=R/'output/release_adversarial/pdf'
cases=[]
for row in json.loads((prior/'report.json').read_text()):
    f=prior/row['name'];cases.append((row['name'],f/'master.docx',f/'actual.pdf',[row['truth']]))
f=O/'two_cells_two_pages';f.mkdir(exist_ok=True)
source='123 × 2 = 246';text='[[*ts*]]'+source+'[[*te*]]';raw='⠸⠩⠀'+noisy(source)+'⠀⠸⠱';at=raw.index('⠈⠡');raw=raw[:at]+'⠨⠌'+raw[at+2:]
doc=Document();doc.add_paragraph(text);doc.save(f/'master.docx')
writer=PdfWriter()
for i,part in enumerate((raw[:at+1],raw[at+1:])):
    p=f/f'part{i}.pdf';braille_pdf(p,[part]);writer.append(PdfReader(p))
with (f/'actual.pdf').open('wb') as out:writer.write(out)
_,prov=load_pdf_provenance(f/'actual.pdf',profile='math')
truth=[]
for page,c in [(1,prov.pages[0].provenance_cells[-1]),(2,prov.pages[1].provenance_cells[0])]:
    truth.append({'page':page,'rectangle':{k:getattr(c,k) for k in ('x0','top','x1','bottom')}})
(f/'truth.json').write_text(json.dumps(truth),encoding='utf8')
cases.append(('two_cells_two_pages',f/'master.docx',f/'actual.pdf',truth))

def check_boxes(path,truth):
    with pdfplumber.open(path) as pdf:
        boxes=[(i,b) for i,page in enumerate(pdf.pages,1) for b in page.rects if isinstance(b.get('stroking_color'),(list,tuple)) and len(b['stroking_color'])==3 and all(abs(a-v)<.01 for a,v in zip(b['stroking_color'],(.12,.48,1)))]
    assert len(boxes)==len(truth),(path,len(boxes),truth)
    for t in truth:
        assert sum(p==t['page'] and all(abs(b[k]-v)<.015 for k,v in t['rectangle'].items()) for p,b in boxes)==1,(path,t)

rows=[]
for name,master,actual,truth in cases:
    dest=O/name;dest.mkdir(exist_ok=True)
    result=validate_document(master,actual);_,prov=load_pdf_provenance(actual,profile='math')
    assert len(result.errors)==1,(name,result)
    assert not result.statistics['unresolved_math_spans'],name
    out=dest/'annotated.pdf';export_annotated_pdf(str(actual),str(out),visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(result,prov)))
    check_boxes(out,truth)
    row={'name':name,'pass':True,'errors':1,'exact_boxes':len(truth),'joined_breaks':result.statistics['joined_physical_page_breaks']}
    if len(sys.argv)>1:
        exe=Path(sys.argv[1]).resolve();env=os.environ.copy();env.update(QT_QPA_PLATFORM='offscreen',LOCALAPPDATA=str(dest/'runtime'))
        p=subprocess.run([str(exe),'--packaging-smoke','--master',str(master),'--braille',str(actual),'--result',str(dest/'exe.json')],env=env,capture_output=True,timeout=120)
        d=json.loads((dest/'exe.json').read_text());assert p.returncode==0 and not d['error'] and not d['annotation_error'],d
        assert d['statistics']['errors']==1 and not d['statistics']['unresolved_math_spans'],d
        check_boxes(d['annotated_pdf'],truth);row['exe_pass']=True
    for i,t in enumerate(truth):
        x=int(t['rectangle']['x0']-12);y=int(t['rectangle']['top']-12)
        subprocess.run(['pdftoppm','-f',str(t['page']),'-l',str(t['page']),'-singlefile','-r','216','-x',str(max(0,x)*3),'-y',str(max(0,y)*3),'-W','300','-H','150','-png',str(out),str(dest/f'crop{i}')],check=True,capture_output=True)
    rows.append(row);print(name,'PASS',flush=True)
(O/'physical_acceptance.json').write_text(json.dumps({'cases':len(rows),'passed':len(rows),'rows':rows},indent=2),encoding='utf8')
