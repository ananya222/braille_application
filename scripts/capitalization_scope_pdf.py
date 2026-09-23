"""Append the tested capitalization scope to the existing math handoff."""
from pathlib import Path
from io import BytesIO
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('Scope','C:/Windows/Fonts/seguisym.ttf'))
body=ParagraphStyle('body',fontName='Scope',fontSize=10,leading=14,spaceAfter=9)
heading=ParagraphStyle('heading',fontName='Scope',fontSize=16,leading=21,spaceAfter=12)
story=[]
def p(text,h=False): story.append(Paragraph(escape(text),heading if h else body))
p('Basic Capitalization',True)
p('Currently supported',True)
p('Rule UEB_8 is reused. Authority: UEB 2024, 8.1.1, 8.2.1 and 8.3.1-3, printed pages 89-90 (PDF 117-118). Dot 6 is required before a single capital letter, including a contraction with a capitalized first letter.')
p('Supported source: ordinary regular-type English words with an initial capital and all remaining letters lowercase, plus isolated A, I and O. Lowercase word starts are checked for unwanted capitals. Examples: Historical Note; Chapter One; A relation is defined; This is a Test. Plain spaces and basic punctuation may precede a word.')
p('The source context must be ordinary UEB, with no active grade-1, numeric, capital-passage or script mode. The checker handles whole prose blocks and the initial prose prefix before explicitly marked Nemeth. Let [[*ts*]]x = 3[[*te*]]. therefore checks Let without interpreting math as literary text.')
rows=[['Case','Production result','Blue-box location'],['Correct capital','No confirmed error','None'],
      ['Wrong indicator','UEB_ERROR / UEB_8','Wrong cell'],['Missing indicator','UEB_ERROR / UEB_8','Following equal letter/contraction cell'],
      ['Unnecessary indicator','UEB_ERROR / UEB_8','Extra dot-6 cell']]
t=Table([[Paragraph(escape(v),body) for v in row] for row in rows],colWidths=[123,158,223])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf2')),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t);story.append(Spacer(1,12))
p('The missing-indicator box marks where the prefix belongs; it does not mean the following letter is wrong. Its anchor is proved by an equal alignment opcode and exact PDF cell provenance. General deletion/insertion handling is unchanged.')
p('Outside current supported scope',True)
p('All-capital words, acronyms, capital passages, internal capitals, non-AIO isolated capitals, foreign/modifier/typeform cases, numeric interactions, arbitrary post-Nemeth context and capitalization inside math are not certified. Unknown mappings are not promoted by this capitalization rule. Broader existing validation behavior is not a claim of coverage here.')
p('Evidence and use',True)
p('Three official examples, seven source contexts and 33 corruption checks passed. The six-line PDF fixture has 99 cells: clean 0 errors; corrupted exactly 3 errors, one each missing/wrong/extra. All three boxes were visually verified. Source: data/basic_capitalization/master.txt or master.json. PDFs: clean.pdf and corrupted.pdf; highlighted export: output/basic_capitalization/corrupted_annotated.pdf.')
p('Source-backend result only: the packaged EXE was not rebuilt. Simple math is unchanged: 118/118 clean cells and six detected substitutions. Chapter 1: 0 confirmed errors, 308 unverified blocks, 4 exclusions, 358 switch pairs, no missing inner blanks. The 29 added unverified blocks require broader capitalization context.')
buffer=BytesIO()
SimpleDocTemplate(buffer,pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=36,bottomMargin=36).build(story)
writer=PdfWriter();writer.append(PdfReader(BytesIO(buffer.getvalue())))
writer.append(PdfReader(ROOT/'reports/Simple_Math_Validation_Scope.pdf'))
with (ROOT/'reports/Simple_Validation_Scope.pdf').open('wb') as out: writer.write(out)
