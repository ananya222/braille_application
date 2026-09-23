"""Leading-sign reconversion regression, including exact raw-cell targets."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from duxbury_spacing_acceptance import master, actual_for, noisy
from braille_app.translation.simple_math import expected
from braille_app.translation.braille_cells import unicode_to_cells
from braille_app.validation.api import adapt_validation_report
from braille_app.validation.validator import BrailleValidator
from braille_app.validation.simple_math_comparison import _artifact_cells

rows = []
for source in ('−4 + 9 = 5', '−12 + 20 = 8', '−7', '−3 + 3 = 0'):
    for spacing in (False, True):
        clean = noisy(source) if spacing else expected(source)
        for mode in ('clean', 'plus_with_indicator', 'reconverted_plus'):
            payload = clean if mode == 'clean' else '⠬' + clean[1 if mode == 'plus_with_indicator' else 2:]
            m = master(source)
            raw = actual_for(m, [payload])
            result = adapt_validation_report(BrailleValidator().validate(m, raw))
            target = raw.index('⠸⠩') + 3
            wanted = [] if mode == 'clean' else [(target, target + 1)]
            assert [(e.actual_cell_start, e.actual_cell_end) for e in result.errors] == wanted, (source, mode, result)
            assert result.statistics['math_spans_evaluated'] == 1
            if wanted:
                assert result.errors[0].actual_braille == (44,)
            rows.append({'source': source, 'spacing': spacing, 'mode': mode, 'errors': len(wanted), 'pass': True})

# The exception must not admit unrelated missing numeric indicators or operands.
for name, source, payload in (
    ('unchanged_minus_missing_indicator', '−4 + 9 = 5', '⠤⠲⠬⠔⠀⠨⠅⠀⠼⠢'),
    ('wrong_operand', '−4 + 9 = 5', '⠬⠒⠬⠔⠀⠨⠅⠀⠼⠢'),
    ('relation_restart_missing', '−4 + 9 = 5', '⠬⠲⠬⠔⠀⠨⠅⠀⠢'),
    ('different_sign', '−4 + 9 = 5', '⠌⠲⠬⠔⠀⠨⠅⠀⠼⠢'),
    ('post_equals_negative', '4 − 9 = −5', '⠼⠲⠤⠔⠀⠨⠅⠀⠬⠢'),
):
    assert _artifact_cells(source, unicode_to_cells(payload)) is None, name
    rows.append({'guard': name, 'pass': True})
out = {'status': 'PASS', 'cases': len(rows), 'rows': rows}
(ROOT / 'reports/unary_reconversion_acceptance.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('Unary reconversion:', len(rows), 'PASS')
