#!/usr/bin/env python3
"""PaperPolice HTML Report Generator v2."""

import json
import sys
import os
import re
from datetime import datetime

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PaperPolice - {filename}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
    --paper:        #f5f1e8;
    --paper-2:      #ece7da;
    --rule:         #1a1a1a14;
    --rule-strong:  #1a1a1a26;
    --ink:          #1a1a1a;
    --ink-soft:     #1a1a1a99;
    --ink-mute:     #1a1a1a66;
    --accent:       #1f3a5f;
    --accent-soft:  #1f3a5f12;
    --accent-line:  #1f3a5f33;
    --remove-bg:    #b4341a0d;
    --remove-mark:  #b4341a;
    --add-bg:       #2c5e2e0d;
    --add-mark:     #2c5e2e;
}}
@media (prefers-color-scheme: dark) {{
    :root {{
        --paper:        #15161a;
        --paper-2:      #1c1d22;
        --rule:         #ffffff14;
        --rule-strong:  #ffffff26;
        --ink:          #ece7da;
        --ink-soft:     #ece7da99;
        --ink-mute:     #ece7da66;
        --accent:       #8fb3dc;
        --accent-soft:  #8fb3dc14;
        --accent-line:  #8fb3dc33;
        --remove-bg:    #ff6b5314;
        --remove-mark:  #ff8a73;
        --add-bg:       #6fc97014;
        --add-mark:     #8fd690;
    }}
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ background: var(--paper); }}
body {{
    font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--ink);
    font-size: 14px;
    line-height: 1.55;
    padding: 56px 24px 96px;
    max-width: 920px;
    margin: 0 auto;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}}

/* ---------- Masthead ---------- */
.mast {{
    border-top: 2px solid var(--ink);
    border-bottom: 1px solid var(--rule-strong);
    padding: 18px 0 22px;
    margin-bottom: 28px;
}}
.mast-row {{
    display: flex; justify-content: space-between; align-items: baseline; gap: 16px;
    font-family: "IBM Plex Mono", monospace; font-size: 11px; letter-spacing: 0.04em;
    color: var(--ink-soft); text-transform: uppercase;
}}
.mast-title {{
    font-family: "Fraunces", Georgia, serif;
    font-weight: 500;
    font-size: 56px;
    line-height: 1.02;
    letter-spacing: -0.02em;
    margin-top: 14px;
    font-variation-settings: "opsz" 96;
}}
.mast-sub {{
    margin-top: 6px;
    font-size: 14px;
    color: var(--ink-soft);
    font-style: italic;
    font-family: "Fraunces", Georgia, serif;
    font-variation-settings: "opsz" 24;
}}
.mast-badges {{
    margin-top: 18px;
    display: flex; flex-wrap: wrap; gap: 8px;
}}
.mast-badges .badge {{
    display: inline-block;
    font-family: "IBM Plex Mono", monospace;
    font-size: 11px; letter-spacing: 0.04em;
    color: var(--accent);
    background: var(--accent-soft);
    border: 1px solid var(--accent-line);
    padding: 4px 10px;
    border-radius: 999px;
    font-feature-settings: "tnum";
}}

/* ---------- Counters ---------- */
.counters {{
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr 1fr;
    column-gap: 0;
    border-bottom: 1px solid var(--rule-strong);
    margin: 28px 0 32px;
}}
.counter {{
    padding: 18px 18px 18px 0;
    border-right: 1px solid var(--rule);
    display: flex; flex-direction: column; gap: 4px;
}}
.counter:last-child {{ border-right: 0; padding-right: 0; }}
.counter + .counter {{ padding-left: 18px; }}
.counter .num {{
    font-family: "Fraunces", Georgia, serif;
    font-variation-settings: "opsz" 96;
    font-size: 44px;
    font-weight: 500;
    line-height: 1;
    letter-spacing: -0.02em;
    color: var(--ink);
    font-feature-settings: "tnum";
}}
.counter.total .num {{ color: var(--accent); }}
.counter .lbl {{
    font-family: "IBM Plex Mono", monospace;
    font-size: 10.5px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink-soft);
}}

/* ---------- Filters ---------- */
.filters {{
    display: flex; gap: 0; flex-wrap: wrap; margin-bottom: 22px;
    border-bottom: 1px solid var(--rule);
}}
.filter-btn {{
    appearance: none; background: transparent; border: 0; cursor: pointer;
    font-family: "IBM Plex Mono", monospace;
    font-size: 11.5px; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--ink-soft);
    padding: 10px 16px 10px 0; margin-right: 18px;
    border-bottom: 2px solid transparent; margin-bottom: -1px;
    transition: color .15s ease;
}}
.filter-btn:hover {{ color: var(--ink); }}
.filter-btn.active {{ color: var(--ink); border-bottom-color: var(--accent); }}

/* ---------- Issues ---------- */
.issues {{ display: flex; flex-direction: column; }}
.issue {{
    border-bottom: 1px solid var(--rule);
    transition: background .15s ease;
}}
.issue:hover {{ background: var(--accent-soft); }}
.issue.open {{ background: var(--accent-soft); }}

.issue-head {{
    display: grid;
    grid-template-columns: 88px 1fr 24px;
    align-items: baseline;
    gap: 16px;
    padding: 16px 4px;
    cursor: pointer;
}}
.issue-tag {{
    font-family: "IBM Plex Mono", monospace;
    font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--accent);
    border-left: 2px solid var(--accent);
    padding-left: 10px;
    line-height: 1.2;
}}
.issue-title {{
    font-family: "Fraunces", Georgia, serif;
    font-variation-settings: "opsz" 24;
    font-size: 18px;
    font-weight: 500;
    line-height: 1.35;
    letter-spacing: -0.005em;
    color: var(--ink);
}}
.issue-chev {{
    font-family: "IBM Plex Mono", monospace;
    font-size: 14px; color: var(--ink-mute);
    text-align: right;
    transition: transform .2s ease;
}}
.issue.open .issue-chev {{ transform: rotate(90deg); color: var(--accent); }}

.issue-body {{ display: none; padding: 4px 4px 28px 4px; }}
.issue.open .issue-body {{ display: block; }}
.issue-body-content {{ padding-left: 88px; }}

/* ---------- Diff ---------- */
.diff-label {{
    font-family: "IBM Plex Mono", monospace;
    font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--ink-mute);
    margin: 14px 0 6px;
}}
.diff-block {{
    font-family: "IBM Plex Mono", monospace;
    font-size: 12.5px; line-height: 1.7;
    border-left: 2px solid var(--rule-strong);
}}
.diff-line {{ padding: 3px 14px; white-space: pre-wrap; word-break: break-word; }}
.diff-line.context {{ color: var(--ink-mute); }}
.diff-line.removed {{ background: var(--remove-bg); color: var(--ink); position: relative; }}
.diff-line.removed::before {{
    content: "−"; position: absolute; left: 2px; color: var(--remove-mark); font-weight: 500;
}}
.diff-line.added {{ background: var(--add-bg); color: var(--ink); position: relative; }}
.diff-line.added::before {{
    content: "+"; position: absolute; left: 2px; color: var(--add-mark); font-weight: 500;
}}
.diff-line.removed .hl {{
    background: transparent;
    color: var(--remove-mark);
    text-decoration: underline;
    text-decoration-color: var(--remove-mark);
    text-decoration-thickness: 1.5px;
    text-underline-offset: 3px;
    font-weight: 500;
}}
.diff-line.added .hl {{
    background: transparent;
    color: var(--add-mark);
    text-decoration: underline;
    text-decoration-color: var(--add-mark);
    text-decoration-thickness: 1.5px;
    text-underline-offset: 3px;
    font-weight: 500;
}}

/* ---------- Advice ---------- */
.advice {{
    margin: 16px 0 4px;
    padding: 14px 18px;
    background: var(--paper-2);
    border-left: 2px solid var(--accent);
    font-size: 13.5px;
    line-height: 1.6;
    color: var(--ink);
}}
.advice strong {{
    display: inline-block;
    font-family: "IBM Plex Mono", monospace;
    font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 6px;
    font-weight: 500;
}}
.advice strong + br {{ display: none; }}

/* ---------- Colophon ---------- */
.colophon {{
    margin-top: 64px;
    padding-top: 18px;
    border-top: 1px solid var(--rule);
    display: flex; justify-content: space-between; align-items: baseline;
    font-family: "IBM Plex Mono", monospace;
    font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink-mute);
}}

@media (max-width: 640px) {{
    body {{ padding: 32px 18px 64px; }}
    .mast-title {{ font-size: 38px; }}
    .counters {{ grid-template-columns: 1fr 1fr; }}
    .counter {{ padding: 14px 14px 14px 0; border-bottom: 1px solid var(--rule); }}
    .counter:nth-child(2n) {{ border-right: 0; }}
    .issue-head {{ grid-template-columns: 1fr 16px; }}
    .issue-tag {{ display: none; }}
    .issue-body-content {{ padding-left: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; animation: none !important; }}
}}
</style>
</head>
<body>

<header class="mast">
    <div class="mast-row">
        <span>{filename}</span>
        <span>{timestamp}</span>
    </div>
    <h1 class="mast-title">PaperPolice</h1>
    <p class="mast-sub">Academic Writing Compliance Report</p>
    <div class="mast-badges">
        <span class="badge">Expression: {expr_count}</span>
        <span class="badge">Abbreviation: {abbr_count}</span>
        <span class="badge">References: {ref_count}</span>
    </div>
</header>

<section class="counters">
    <div class="counter total"><div class="num">{total}</div><div class="lbl">Total Issues</div></div>
    <div class="counter"><div class="num">{expr_count}</div><div class="lbl">Expression</div></div>
    <div class="counter"><div class="num">{abbr_count}</div><div class="lbl">Abbreviation</div></div>
    <div class="counter"><div class="num">{ref_count}</div><div class="lbl">References</div></div>
</section>

<nav class="filters" role="tablist">
    <button class="filter-btn active" data-filter="all">All ({total})</button>
    <button class="filter-btn" data-filter="EXPR">Expression ({expr_count})</button>
    <button class="filter-btn" data-filter="ABBR">Abbreviation ({abbr_count})</button>
    <button class="filter-btn" data-filter="REF">References ({ref_count})</button>
</nav>

<main class="issues">
{issues_html}
</main>

<footer class="colophon">
    <span>Generated by PaperPolice</span>
    <span>{filename} &nbsp;|&nbsp; {timestamp}</span>
</footer>

<script>
document.querySelectorAll('.issue-head').forEach(h => {{
    h.addEventListener('click', () => h.parentElement.classList.toggle('open'));
}});
document.querySelectorAll('.filter-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const t = btn.dataset.filter;
        document.querySelectorAll('.issue').forEach(el => {{
            el.style.display = (t === 'all' || el.dataset.check === t) ? '' : 'none';
        }});
    }});
}});
</script>
</body>
</html>'''


def escape_html(text):
    if not text:
        return ''
    return (text.replace('&', '&amp;').replace('<', '&lt;')
                .replace('>', '&gt;').replace('"', '&quot;'))


def highlight_in_sentence(sentence, target, css_class='hl'):
    """Highlight target word in sentence, return HTML."""
    if not target or not sentence:
        return escape_html(sentence)
    escaped_sent = escape_html(sentence)
    escaped_target = escape_html(target)
    # Replace first match
    idx = escaped_sent.lower().find(escaped_target.lower())
    if idx >= 0:
        before = escaped_sent[:idx]
        match = escaped_sent[idx:idx+len(escaped_target)]
        after = escaped_sent[idx+len(escaped_target):]
        return f'{before}<span class="{css_class}">{match}</span>{after}'
    return escaped_sent


def generate_issue_html(issue, index):
    check_id = issue['id']
    mode = issue.get('mode', 'text')

    body_html = ''

    if mode == 'diff':
        # Mode A: diff display with explicit modification
        prev_sent = issue.get('prev_sent', '')
        current_sent = issue.get('current_sent', '')
        next_sent = issue.get('next_sent', '')
        original = issue.get('original', '')
        replacement = issue.get('replacement', '')
        modified_sent = issue.get('modified_sent', '')

        # Before
        before_block = '<div class="diff-label">Before:</div><div class="diff-block">'
        if prev_sent:
            before_block += f'<div class="diff-line context">{escape_html(prev_sent)}</div>'
        before_block += f'<div class="diff-line removed">{highlight_in_sentence(current_sent, original, "hl")}</div>'
        if next_sent:
            before_block += f'<div class="diff-line context">{escape_html(next_sent)}</div>'
        before_block += '</div>'

        # Issue & Suggestion
        advice_block = f'<div class="advice"><strong>Issue & Suggestion:</strong><br>{escape_html(issue.get("description", ""))}</div>'

        # After
        after_block = '<div class="diff-label">After:</div><div class="diff-block">'
        if prev_sent:
            after_block += f'<div class="diff-line context">{escape_html(prev_sent)}</div>'
        after_block += f'<div class="diff-line added">{highlight_in_sentence(modified_sent, replacement, "hl")}</div>'
        if next_sent:
            after_block += f'<div class="diff-line context">{escape_html(next_sent)}</div>'
        after_block += '</div>'

        body_html = before_block + advice_block + after_block

    else:
        # Mode B: text-only suggestion
        desc = issue.get('description', '')
        body_html = f'<div class="advice"><strong>Issue & Suggestion:</strong><br>{escape_html(desc)}</div>'

    return f'''<article class="issue" data-check="{check_id}">
    <header class="issue-head">
        <span class="issue-tag">{check_id}</span>
        <span class="issue-title">{escape_html(issue.get("name", ""))}</span>
        <span class="issue-chev">›</span>
    </header>
    <div class="issue-body">
        <div class="issue-body-content">{body_html}</div>
    </div>
</article>'''


def generate_report(issues_json_path, output_path=None):
    with open(issues_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filename = os.path.basename(data['file'])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    issues = data['issues']

    issues_html_parts = [generate_issue_html(iss, i) for i, iss in enumerate(issues)]

    # Count by dimension
    expr_count = sum(1 for i in issues if i['id'] == 'EXPR')
    abbr_count = sum(1 for i in issues if i['id'] == 'ABBR')
    ref_count = sum(1 for i in issues if i['id'] == 'REF')

    html = HTML_TEMPLATE.format(
        filename=filename,
        timestamp=timestamp,
        total=data['total_issues'],
        expr_count=expr_count,
        abbr_count=abbr_count,
        ref_count=ref_count,
        issues_html='\n'.join(issues_html_parts),
    )

    if output_path is None:
        base = os.path.splitext(data['file'])[0]
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        output_path = f'{base}_PaperPolice_{ts}.html'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 gen_report.py <issues.json> [output.html]")
        sys.exit(1)

    json_path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    path = generate_report(json_path, output)
    print(f"Report generated: {path}")
