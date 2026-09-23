"""Build the concise tester handoff, using recorded acceptance evidence."""
from pathlib import Path
from html import escape
import json,shutil
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('Scope','C:/Windows/Fonts/seguisym.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='S',fontName='Scope',fontSize=10,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='H',fontName='Scope',fontSize=16,leading=21,spaceAfter=12))
story=[]
def p(text,style='S'): story.append(Paragraph(escape(text),styles[style]))
p('Simple math validation scope','H')
p('Tester handoff | 11 September 2026 | Source backend acceptance; packaged EXE not rebuilt')
p('Currently supported: explicit addition, subtraction, unary negative, multiplication cross, division sign and equality in the closed grammar below. Square roots are outside current supported scope because the source interface does not preserve vinculum information.')
rows=[['Construct','Example','Rule and check'],
['Addition','2 + 3 = 5','20.1: plus; 3.3.1/3.4.1: numeric context'],
['Subtraction','8 − 3 = 5','20.1: minus, no operation spaces'],
['Unary negative','−2; x = −2','3.3.1: indicator after leading minus'],
['Multiplication','4 × 3 = 12','Rule 20: explicit cross cells'],
['Division','8 ÷ 2 = 4','Rule 20: explicit division cells'],
['Equality','x = y','21.13 and 6.4.7: comparison context'],
['Square root','No admitted source form','16.1.1/16.1.2 require known print structure']]
t=Table([[Paragraph(escape(v),styles['S']) for v in row] for row in rows],colWidths=[100,133,271])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf2')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story.append(t);story.append(Spacer(1,14))
p('Source grammar and context','H')
p('One complete expression per explicit [[*ts*]] ... [[*te*]] span. Operands: unsigned ASCII integers or single lowercase English variables. Mixed number/letter operands are allowed. Binary operators: +, −, ×, ÷. At most one = with a complete expression on each side. Unary − is allowed only initially or immediately after =. Regular-type, baseline linear math only.')
p('No grouping or implicit multiplication. Spaces may separate source tokens but cannot join two operands. Keep sentence punctuation outside the markers. Do not wrap an expression across physical Braille lines for this acceptance set. Arithmetic truth is not checked: 2 = 3 can be faithfully transcribed without a transcription error.')
story.append(PageBreak())
p('Scope limitations and failure behavior','H')
p('Outside current supported scope: fractions, slash division, multiplication dots, implied multiplication, inequalities, membership, scripts, functions, uppercase/typeform math, matrices, vectors, grouping, nested structures, decimals, consecutive signs and unknown radicals. Plain √x or √(x + 1) does not establish a vinculum and remains unverified.')
p('A failed complete parse is REVIEW unless an existing independent rule proves that whole structure. REVIEW means unverified, not incorrect. The new grammar never certifies an unsupported suffix or derives correctness from Duxbury.')
p('Verified error scope: nonblank cell substitutions in the supported payload, including operators, numeric and letter cells. These produce NEMETH_ERROR with NEMETH_SIMPLE_LINEAR_001 and exact actual-cell ranges. Arbitrary insertions, deletions and spacing-only defects are not certified by this milestone; existing alignment filters may suppress them. Source extraction, typography and physical line-runover interpretation remain limitations.')
p('Acceptance evidence','H')
p('Seven official examples and twelve unseen/literal rule applications passed. Every nonblank payload cell was separately corrupted and production reported one localized error. Twenty-three parser exclusions were tested; nonempty excluded sources were checked through production for conservative fallback.')
e=json.loads((ROOT/'reports/simple_math_acceptance.json').read_text(encoding='utf8'))
p('Public fixture: seven expressions, 118 cells. Correct PDF: 0 errors, 0 reviews, 118/118 matching. Corrupted PDF: six deliberately changed cells, six confirmed errors and six blue boxes. Export re-extraction preserved cells; unmatched provenance and unexplained offsets both 0.')
p('Using the fixtures','H')
p('data/simple_math/master.txt contains the exact marked source; paste each line into a separate Word paragraph and save as DOCX for the GUI. master.json is the structured API input used by the acceptance script. Pair with correct.pdf or corrupted.pdf. PDFs visibly show Braille dots, with the established NABCC extraction font mapping. No radical example is included.')
p('Run scripts/simple_math_acceptance.py --validate with the project Python to repeat the PDF acceptance. The installed packaged EXE has not been updated by this task. Use the source backend for these results until a frozen build is separately accepted.')
p('Authorities','H')
p('Nemeth_2022.pdf: 3.3.1, 3.4.1 (3-3, 3-11); 6.3.1, 6.4.7 (6-6, 6-12); Rule 20 and 20.1 (20-1 to 20-4); 21.13 (21-15); 16.1 (16-1 to 16-3). October 2025 errata: amended 4.2 governs the existing inner switch blanks. Test oracles are standard examples or direct applications, not generator output.')
out=ROOT/'reports/Simple_Math_Validation_Scope.pdf'
SimpleDocTemplate(str(out),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=40,bottomMargin=40).build(story)
shutil.copyfile(out,ROOT/'reports/Simple_Math_Supported_Scope.pdf')
