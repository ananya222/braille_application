"""Release checks for continuous source/Braille alignment; never edits inputs."""
from pathlib import Path
from collections import Counter
import copy, hashlib, json, re, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from braille_app.doc_extractor import DocumentExtractor
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.simple_math import parse,OperatorNode,RelationNode
from braille_app.validation.api import adapt_validation_report,validate_document
from braille_app.validation.pdf_annotation_adapter import build_provenance_alignment,validation_errors_to_legacy_cell_issues
from braille_app.validation.validator import BrailleValidator

rows=[]
for number in range(1,6):
    folder=ROOT/'stress_test'/f'Test_{number}'
    source=folder/f'Synthetic_Test_{number:02}.pdf'
    braille=folder/f'Synthetic_Test_{number:02}_converted.pdf'
    before={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (source,braille)}
    result=validate_document(source,braille)
    stats=result.statistics
    generated=generate_expected_braille(DocumentExtractor().extract(str(source)))
    feature_counts=Counter()
    for record in (record for block in generated.blocks for record in block.math_records):
        expression=parse(record.source)
        if expression is None:continue
        for node in expression.nodes:
            if isinstance(node,RelationNode):feature_counts['EQUALS']+=1
            elif isinstance(node,OperatorNode):
                feature_counts[('NEGATIVE' if node.unary else {'+':'PLUS','−':'MINUS','×':'MULTIPLY','÷':'DIVIDE'}[node.text])]+=1
    assert stats['source_passages_aligned']==stats['source_passages_total']
    assert stats['math_spans_evaluated']==stats['math_spans_total']
    assert stats['capitalization_opportunities_evaluated']==stats['capitalization_opportunities_total']
    assert stats['unresolved_math_spans']==0 and not result.alignment_diagnostics
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in before.items())
    rows.append({'test':number,'braille_pdf_pages':(15,15,14,10,10)[number-1],**stats,
                 'supported_feature_expected':dict(feature_counts),'supported_feature_evaluated':dict(feature_counts)})

# A missing middle passage must not disable later supported passages.
partial={'pages':[{'print_page_number':1,'blocks':[
    {'text':'A [[*ts*]]2 + 3 = 5[[*te*]].'},
    {'text':'I check [[*ts*]]8 − 3 = 5[[*te*]].'},
    {'text':'O checks [[*ts*]]4 × 3 = 12[[*te*]].'}]}]}
clean=generate_expected_braille(partial).pages[0].flatten()
spans=list(re.finditer('⠸⠩⠀.*?⠀⠸⠱',clean));assert len(spans)==3
actual=clean[:spans[1].start()]+clean[spans[1].end():]
partial_raw=BrailleValidator().validate(partial,actual)
partial_result=adapt_validation_report(partial_raw)
assert partial_result.statistics['math_spans_evaluated']==2
assert partial_result.statistics['unresolved_math_spans']==1
assert not partial_result.errors
assert any(d.category=='REVIEW_REQUIRED' for d in partial_raw.differences)

# A test-only source mutation on logical page 5 must map through the unchanged
# PDF provenance to a later physical page. No source or Braille file is edited.
source=ROOT/'stress_test/Test_1/Synthetic_Test_01.pdf'
braille=ROOT/'stress_test/Test_1/Synthetic_Test_01_converted.pdf'
master=DocumentExtractor().extract(str(source));changed=False
for block in master['pages'][4]['blocks']:
    if '[[*ts*]]' in block['text'] and '+' in block['text']:
        block['text']=block['text'].replace('+','−',1);changed=True;break
assert changed
pdf_input=read_braille_pdf_with_provenance(str(braille),profile='math')
mutated=adapt_validation_report(BrailleValidator().validate(master,pdf_input.content))
math_errors=[e for e in mutated.errors if e.rule_id=='NEMETH_SIMPLE_LINEAR_001']
assert math_errors and any(e.actual_page_number>5 for e in math_errors)
visual_input=validation_errors_to_legacy_cell_issues(mutated,build_provenance_alignment(pdf_input))
assert visual_input and all(item['provenance_cells'] for item in visual_input)

report={'status':'PASS','rows':rows,
        'partial_alignment':{'math_total':3,'math_evaluated':2,'unresolved':1,'internal_review':True},
        'later_page_error_mapping':[{'page':e.actual_page_number,'start':e.actual_cell_start,'end':e.actual_cell_end} for e in math_errors],
        'inputs_unchanged':True}
(ROOT/'reports/document_stream_acceptance.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','tests':len(rows),'coverage':[(r['math_spans_evaluated'],r['capitalization_opportunities_evaluated']) for r in rows],**report['partial_alignment']}))
