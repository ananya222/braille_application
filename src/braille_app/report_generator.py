import json
import difflib
from collections import defaultdict
from typing import Dict, Any, List

def generate_inline_diff(expected: str, actual: str) -> str:
    if not expected:
        return f'<span class="diff-inserted">{actual}</span>'
    if not actual:
        return f'<span class="diff-deleted">{expected}</span>'
    
    exp_words = expected.split()
    act_words = actual.split()
    
    matcher = difflib.SequenceMatcher(None, exp_words, act_words)
    opcodes = matcher.get_opcodes()
    
    html_parts = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            html_parts.append(" ".join(exp_words[i1:i2]))
        elif tag == 'replace':
            html_parts.append(f'<span class="diff-deleted">{" ".join(exp_words[i1:i2])}</span>')
            html_parts.append(f'<span class="diff-inserted">{" ".join(act_words[j1:j2])}</span>')
        elif tag == 'delete':
            html_parts.append(f'<span class="diff-deleted">{" ".join(exp_words[i1:i2])}</span>')
        elif tag == 'insert':
            html_parts.append(f'<span class="diff-inserted">{" ".join(act_words[j1:j2])}</span>')
            
    return " ".join(html_parts)

class ReportGenerator:
    def __init__(self):
        self.html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Braille Validation Dashboard</title>
<style>
    :root {{
        --bg-color: #0b0f19;
        --card-bg: #151c2c;
        --text-main: #f3f4f6;
        --text-muted: #9ca3af;
        --accent: #8b5cf6;
        --danger: #ef4444;
        --warning: #f59e0b;
        --success: #10b981;
        --info: #3b82f6;
        --border-color: #1f2937;
    }}
    
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    body {{
        background-color: var(--bg-color);
        color: var(--text-main);
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        padding: 40px 20px;
        min-height: 100vh;
    }}
    
    .container {{
        max-width: 1200px;
        margin: 0 auto;
    }}
    
    header {{
        margin-bottom: 40px;
        text-align: center;
        background: linear-gradient(135deg, #1e1b4b 0%, #151c2c 100%);
        padding: 30px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }}
    
    header h1 {{
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.05em;
        background: linear-gradient(to right, #a78bfa, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }}
    
    header p {{
        color: var(--text-muted);
        font-size: 1rem;
    }}
    
    /* Provisional assumptions banner */
    .banner {{
        background: linear-gradient(135deg, #2e1a05 0%, #1c150c 100%);
        border-left: 6px solid var(--warning);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
        border-top: 1px solid #3e2e1a;
        border-right: 1px solid #3e2e1a;
        border-bottom: 1px solid #3e2e1a;
    }}
    
    .banner h2 {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.4rem;
        color: var(--warning);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    .banner-warning-text {{
        color: #fbd38d;
        margin-bottom: 20px;
        font-size: 0.95rem;
        background: rgba(245, 158, 11, 0.1);
        padding: 12px;
        border-radius: 8px;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }}
    
    /* BANA Spacing Table */
    .banner-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .banner-table th, .banner-table td {{
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid #2d261b;
        font-size: 0.9rem;
    }}
    
    .banner-table th {{
        background-color: rgba(0, 0, 0, 0.4);
        color: var(--text-main);
        font-weight: 600;
    }}
    
    .badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }}
    
    .badge-sourced {{
        background: rgba(16, 185, 129, 0.2);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    
    .badge-assumed-high-med {{
        background: rgba(59, 130, 246, 0.2);
        color: var(--info);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }}
    
    .badge-assumed-med {{
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    
    .badge-assumed-low {{
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}

    /* Grid layout */
    .grid-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
    }}
    
    .summary-card {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    
    .summary-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
    }}
    
    .summary-card h3 {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-muted);
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .summary-card .number {{
        font-size: 3rem;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
        line-height: 1;
        margin-bottom: 10px;
    }}
    
    .card-high-confidence {{ border-top: 4px solid var(--danger); }}
    .card-high-confidence .number {{ color: var(--danger); }}
    .card-needs-review {{ border-top: 4px solid var(--warning); }}
    .card-needs-review .number {{ color: var(--warning); }}
    .card-alignment-failure {{ border-top: 4px solid var(--info); }}
    .card-alignment-failure .number {{ color: var(--info); }}
    .card-ignored {{ border-top: 4px solid var(--success); }}
    .card-ignored .number {{ color: var(--success); }}
    
    .summary-card ul {{
        list-style: none;
        margin-top: 10px;
    }}
    
    .summary-card li {{
        font-size: 0.85rem;
        color: var(--text-muted);
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        border-bottom: 1px solid #1f2937;
    }}

    .summary-card li span {{
        font-weight: bold;
        color: var(--text-main);
    }}
    
    /* Patterns Section */
    .patterns-box {{
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 45px;
    }}
    
    .patterns-box h2 {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.3rem;
        margin-bottom: 16px;
        color: #c084fc;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
    }}
    
    .pattern-item {{
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid #a855f7;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }}
    
    /* Findings Sections */
    .findings-group {{
        margin-bottom: 24px;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }}
    
    .collapsible {{
        background-color: var(--card-bg);
        color: var(--text-main);
        cursor: pointer;
        padding: 20px 24px;
        width: 100%;
        border: none;
        text-align: left;
        outline: none;
        font-family: 'Outfit', sans-serif;
        font-size: 1.2rem;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: background-color 0.2s;
    }}
    
    .collapsible:after {{
        content: '\\25BC';
        font-size: 0.8rem;
        color: var(--text-muted);
        transition: transform 0.2s;
    }}
    
    .active:after {{
        transform: rotate(-180deg);
    }}
    
    .collapsible:hover {{
        background-color: #1c253b;
    }}
    
    .content {{
        background-color: #101622;
        border-top: 1px solid var(--border-color);
        transition: max-height 0.2s ease-out;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    
    th, td {{
        padding: 14px 20px;
        text-align: left;
        font-size: 0.9rem;
    }}
    
    th {{
        background-color: rgba(0, 0, 0, 0.25);
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        border-bottom: 1px solid var(--border-color);
    }}
    
    tr {{
        border-bottom: 1px solid var(--border-color);
        transition: background-color 0.15s;
    }}
    
    tr:hover td {{
        background-color: rgba(255,255,255,0.01);
    }}
    
    /* Inline differences styling */
    .diff-deleted {{
        background-color: rgba(239, 68, 68, 0.25);
        color: #f87171;
        text-decoration: line-through;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 4px;
    }}
    
    .diff-inserted {{
        background-color: rgba(16, 185, 129, 0.25);
        color: #34d399;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
    }}
    
    .label-tag {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    
    .tag-trans {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .tag-form {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }}
    .tag-brf {{ background: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }}

    @media print {{
        body {{ background-color: #fff; color: #000; padding: 0; }}
        .summary-card, .findings-group, .patterns-box, .banner {{
            background: #fff !important;
            color: #000 !important;
            border: 1px solid #000 !important;
            box-shadow: none !important;
            page-break-inside: avoid;
        }}
        .content {{ display: block !important; }}
        .collapsible:after {{ display: none; }}
        .diff-deleted {{ background: none; color: #7f1d1d; text-decoration: line-through; }}
        .diff-inserted {{ background: none; color: #14532d; font-weight: bold; }}
    }}
</style>
</head>
<body>

<div class="container">
    <header>
        <h1>Braille Validation Dashboard</h1>
        <p>Comprehensive layout compliance & translation error report</p>
    </header>

    {banner_html}

    <div class="section" id="summary">
        <div class="grid-container">
            <div class="summary-card card-high-confidence">
                <h3>High Confidence Issues</h3>
                <div class="number">{hc_total}</div>
                <ul>
                    <li>Translation: <span>{hc_trans}</span></li>
                    <li>Formatting: <span>{hc_form}</span></li>
                    <li>BRF Structure: <span>{hc_brf}</span></li>
                </ul>
            </div>
            
            <div class="summary-card card-needs-review">
                <h3>Needs Review</h3>
                <div class="number">{nr_total}</div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 5px;">Requires human proofreader review</p>
            </div>
            
            <div class="summary-card card-alignment-failure">
                <h3>Alignment Failures</h3>
                <div class="number">{align_total}</div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 5px;">Unvalidated segments (count mismatch)</p>
            </div>
            
            <div class="summary-card card-ignored">
                <h3>Ignored Differences</h3>
                <div class="number">{ignored_total}</div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 5px;">Allowlisted differences</p>
            </div>
        </div>
    </div>

    <div class="patterns-box">
        <h2>Top-Level Pattern Collapses</h2>
        {patterns_html}
    </div>

    <div class="section" id="findings">
        {findings_html}
    </div>
</div>

<script>
var coll = document.getElementsByClassName("collapsible");
for (var i = 0; i < coll.length; i++) {{
  coll[i].addEventListener("click", function() {{
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.maxHeight) {{
      content.style.maxHeight = null;
      content.style.display = "none";
    }} else {{
      content.style.display = "block";
      content.style.maxHeight = content.scrollHeight + "px";
    }}
  }});
}}
</script>

</body>
</html>
"""

    def generate_report(self, brf_results: Dict[str, Any], diff_results: Dict[str, Any], format_results: Dict[str, Any]) -> str:
        # 1. Provisional Spacing / Indentation Assumptions Table
        warnings = []
        if "provisional_warning" in format_results:
            warnings.append(format_results['provisional_warning'])
            
        banner_table = """
        <table class="banner-table">
            <thead>
                <tr>
                    <th>Formatting Rule Category</th>
                    <th>Current Configured Rules</th>
                    <th>BANA Rules Basis / Confidence Level</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Paragraph Indentation</strong></td>
                    <td>Cell 3 start, Cell 1 runover</td>
                    <td><span class="badge badge-sourced">SOURCED (High Confidence)</span> - Standard literary UEB rules.</td>
                </tr>
                <tr>
                    <td><strong>List Indentation</strong></td>
                    <td>Valid starts: cell 1/3, Runovers: cell 3/5</td>
                    <td><span class="badge badge-assumed-high-med">ASSUMED (High-Medium Confidence)</span> - Standard nested layout formats.</td>
                </tr>
                <tr>
                    <td><strong>Heading 2/3 Spacing</strong></td>
                    <td>H2/H3: &ge; 1 blank line before</td>
                    <td><span class="badge badge-assumed-med">ASSUMED (Medium Confidence)</span> - Spacing varies across textbook styles.</td>
                </tr>
                <tr>
                    <td><strong>Heading 1 Spacing</strong></td>
                    <td>H1: &ge; 2 blank lines before</td>
                    <td><span class="badge badge-assumed-low">ASSUMED (Low Confidence)</span> - High risk. Bypassed when heading falls at the very top of a braille page.</td>
                </tr>
                <tr>
                    <td><strong>Heading Level Indents</strong></td>
                    <td>Visual distinction required between levels</td>
                    <td><span class="badge badge-assumed-low">ASSUMED (Low Confidence)</span> - Style profiles are Duxbury template dependent.</td>
                </tr>
            </tbody>
        </table>
        """
        
        # BRF parser configuration mismatches if present
        calib_mismatch = ""
        if brf_results.get("detected_patterns"):
            mismatch_items = []
            for pat in brf_results["detected_patterns"]:
                mismatch_items.append(f"<div class='pattern-item'>{pat.get('message', '')}</div>")
            calib_mismatch = f"<div>{''.join(mismatch_items)}</div>"
            
        banner_html = f"""
        <div class="banner">
            <h2>Provisional Assumptions & Calibration Mismatches</h2>
            <div class="banner-warning-text">
                <strong>Important:</strong> Spacing and indentation rules below are provisional assumptions. Treat layout verification findings as PROVISIONAL until manual cross-checks are done.
            </div>
            {calib_mismatch}
            {banner_table}
        </div>
        """

        # 2. Count calculations
        hc_trans = 0
        hc_form = 0
        hc_brf = sum(len(p.get("high_confidence", [])) for p in brf_results.get("pages", []))
        
        nr_total = sum(len(p.get("needs_review_reported", [])) for p in brf_results.get("pages", []))
        align_total = 0
        ignored_total = 0

        grouped_findings = defaultdict(list)

        # Translation Diffs
        for diff in diff_results.get("diffs", []):
            conf = diff.get("confidence")
            if conf == "high_confidence":
                hc_trans += 1
            elif conf == "needs_review":
                nr_total += 1
            elif conf == "alignment_failure":
                align_total += 1
            elif conf == "ignored":
                ignored_total += 1
            grouped_findings[conf].append({"source": "Translation", **diff})

        # Formatting Diffs
        for diff in format_results.get("diffs", []):
            conf = diff.get("confidence")
            if conf == "high_confidence":
                hc_form += 1
            elif conf == "needs_review":
                nr_total += 1
            elif conf == "alignment_failure":
                align_total += 1
            elif conf == "ignored":
                ignored_total += 1
            grouped_findings[conf].append({"source": "Formatting", **diff})

        # BRF Parser Diffs
        for p in brf_results.get("pages", []):
            pidx = p.get("page_index")
            for hc in p.get("high_confidence", []):
                grouped_findings["high_confidence"].append({
                    "source": "BRF Structure", "type": "brf_error", "location": f"Page {pidx}",
                    "expected": "", "actual": hc
                })
            for nr in p.get("needs_review_reported", []):
                grouped_findings["needs_review"].append({
                    "source": "BRF Structure", "type": nr.get("type", "brf_issue"), "location": f"Page {pidx}",
                    "expected": "", "actual": nr.get("message", "")
                })

        hc_total = hc_trans + hc_form + hc_brf

        # 3. Pattern summary
        patterns_list = []
        for p in diff_results.get("patterns", []):
            patterns_list.append(f"<div class='pattern-item'>{p.get('message')}</div>")
        for p in format_results.get("patterns", []):
            patterns_list.append(f"<div class='pattern-item'>{p.get('message')}</div>")
            
        if patterns_list:
            patterns_html = "".join(patterns_list)
        else:
            patterns_html = "<p style='color: var(--text-muted); font-size: 0.9rem;'>No systemic pattern collapses detected.</p>"

        # 4. Findings sections
        findings_html = ""
        # The prompt requires: "ignored/ok content starts collapsed, findings start expanded"
        for group in ["high_confidence", "alignment_failure", "needs_review", "ignored"]:
            items = grouped_findings.get(group, [])
            if not items:
                continue
            
            # Non-ignored findings start expanded
            is_ignored = (group == "ignored")
            content_style = 'style="display: none;"' if is_ignored else 'style="display: block;"'
            coll_class = 'collapsible' if is_ignored else 'collapsible active'
            
            findings_html += f'<div class="findings-group">\n'
            findings_html += f'<button class="{coll_class}">{group.replace("_", " ").title()} ({len(items)})</button>\n'
            findings_html += f'<div class="content" {content_style}>\n<table>\n'
            findings_html += '<tr><th style="width: 15%;">Source</th><th style="width: 20%;">Type</th><th style="width: 15%;">Location</th><th>Expected vs Actual (Diff)</th></tr>\n'
            
            for item in items:
                source = item.get("source", "")
                source_tag = f'<span class="label-tag tag-trans">Translation</span>' if source == "Translation" else \
                             f'<span class="label-tag tag-form">Formatting</span>' if source == "Formatting" else \
                             f'<span class="label-tag tag-brf">Structure</span>'
                             
                exp_text = item.get("expected", "")
                act_text = item.get("actual", "")
                diff_formatted = generate_inline_diff(exp_text, act_text)
                
                findings_html += '<tr>'
                findings_html += f'<td>{source_tag}</td>'
                findings_html += f'<td><code style="color: #c084fc;">{item.get("type", "")}</code></td>'
                findings_html += f'<td>{item.get("location", "")}</td>'
                findings_html += f'<td>{diff_formatted}</td>'
                findings_html += '</tr>\n'
            findings_html += '</table>\n</div>\n</div>\n'

        return self.html_template.format(
            banner_html=banner_html,
            hc_total=hc_total,
            hc_trans=hc_trans,
            hc_form=hc_form,
            hc_brf=hc_brf,
            nr_total=nr_total,
            align_total=align_total,
            ignored_total=ignored_total,
            patterns_html=patterns_html,
            findings_html=findings_html
        )
