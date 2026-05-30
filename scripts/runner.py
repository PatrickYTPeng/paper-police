#!/usr/bin/env python3
"""PaperPolice Runner - Load all check modules and aggregate results.
Supports input: a single .tex file or a directory containing multiple .tex files.
"""

import sys
import os
import re
import json
import importlib
import tempfile
from pathlib import Path
from datetime import datetime

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from parse_tex import parse


def load_checks():
    """Auto-scan the checks/ directory and import all check modules."""
    checks_dir = os.path.join(SCRIPT_DIR, 'checks')
    modules = []
    for fname in sorted(os.listdir(checks_dir)):
        if fname.endswith('.py') and fname != '__init__.py':
            mod_name = fname[:-3]
            mod = importlib.import_module(f'checks.{mod_name}')
            if hasattr(mod, 'check') and hasattr(mod, 'CHECK_ID'):
                modules.append(mod)
    return modules


def find_main_tex(directory):
    """Find the main tex file in a directory (the one containing \\begin{document})."""
    candidates = []
    for f in os.listdir(directory):
        if f.endswith('.tex'):
            fpath = os.path.join(directory, f)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
            if r'\begin{document}' in content:
                candidates.append(fpath)
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        # Prefer files named main/paper/arxiv
        for c in candidates:
            base = os.path.basename(c).lower()
            if any(k in base for k in ['main', 'paper', 'arxiv', 'manuscript']):
                return c
        return candidates[0]
    return None


def merge_inputs(main_tex_path):
    """Recursively merge \\input{} referenced files and return the merged temp file path."""
    base_dir = os.path.dirname(os.path.abspath(main_tex_path))
    visited = set()

    def resolve(tex_content, current_dir):
        # Handle \input{} references
        pattern = r'\\input\{([^}]+)\}'
        def replacer(m):
            fname = m.group(1)
            if not fname.endswith('.tex') and not fname.endswith('.bbl'):
                fname += '.tex'
            fpath = os.path.normpath(os.path.join(current_dir, fname))
            # Prevent circular references
            if fpath in visited:
                return ''
            visited.add(fpath)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return resolve(content, os.path.dirname(fpath))
            else:
                return m.group(0)  # Keep as-is
        tex_content = re.sub(pattern, replacer, tex_content)

        # Handle \bibliography{} - look for corresponding .bbl file
        def bib_replacer(m):
            bib_name = m.group(1)
            bbl_path = os.path.normpath(os.path.join(current_dir, bib_name + '.bbl'))
            if bbl_path in visited:
                return m.group(0)
            visited.add(bbl_path)
            if os.path.exists(bbl_path):
                with open(bbl_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            # Also try main.bbl in same directory
            main_bbl = os.path.normpath(os.path.join(current_dir, 'main.bbl'))
            if main_bbl not in visited and os.path.exists(main_bbl):
                visited.add(main_bbl)
                with open(main_bbl, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            return m.group(0)
        tex_content = re.sub(r'\\bibliography\{([^}]+)\}', bib_replacer, tex_content)

        return tex_content

    with open(main_tex_path, 'r', encoding='utf-8', errors='ignore') as f:
        main_content = f.read()

    visited.add(os.path.abspath(main_tex_path))
    merged = resolve(main_content, base_dir)

    # Write to temp file
    tmp_path = os.path.join(tempfile.gettempdir(), 'paperpolice_merged.tex')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(merged)

    return tmp_path


def resolve_input(path):
    """Resolve user input: return single file directly, or find main file and merge for directories."""
    path = os.path.abspath(path)

    if os.path.isfile(path):
        if not path.endswith('.tex'):
            print(f"Error: {path} is not a .tex file")
            sys.exit(1)
        # Check if there are \input{} references to merge
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if r'\input{' in content or r'\input {' in content:
            print(f"Detected \\input references, merging files...")
            merged = merge_inputs(path)
            print(f"Merge complete: {merged}")
            return merged, path
        return path, path

    elif os.path.isdir(path):
        main_tex = find_main_tex(path)
        if not main_tex:
            print(f"Error: no main .tex file containing \\begin{{document}} found in {path}")
            sys.exit(1)
        print(f"Main file found: {main_tex}")
        merged = merge_inputs(main_tex)
        print(f"Merge complete: {merged}")
        return merged, main_tex

    else:
        print(f"Error: {path} does not exist")
        sys.exit(1)


def run(input_path):
    """Run all checks."""
    # Resolve input
    tex_path, original_path = resolve_input(input_path)

    # Parse LaTeX
    parsed = parse(tex_path)

    # Load and execute all checks
    checks = load_checks()
    all_issues = []

    for mod in checks:
        try:
            issues = mod.check(parsed)
            all_issues.extend(issues)
        except Exception as e:
            print(f"Warning: {mod.CHECK_ID} ({mod.CHECK_NAME}) error: {e}")

    # Sort by dimension
    dim_order = {'EXPR': 0, 'ABBR': 1, 'REF': 2}
    all_issues.sort(key=lambda x: dim_order.get(x['id'], 9))

    # Count by dimension
    expr_count = sum(1 for i in all_issues if i['id'] == 'EXPR')
    abbr_count = sum(1 for i in all_issues if i['id'] == 'ABBR')
    ref_count = sum(1 for i in all_issues if i['id'] == 'REF')

    output = {
        'file': original_path,
        'timestamp': datetime.now().isoformat(),
        'total_issues': len(all_issues),
        'expr_count': expr_count,
        'abbr_count': abbr_count,
        'ref_count': ref_count,
        'checks_run': [{'id': m.CHECK_ID, 'name': m.CHECK_NAME} for m in checks],
        'issues': all_issues,
        'references': parsed.get('references', {}),  # For LLM Step 5 verification
    }

    # Output JSON to temp directory
    json_path = os.path.join(tempfile.gettempdir(), 'paperpolice_issues.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Check complete: {len(all_issues)} issues (Expression: {expr_count}, Abbreviation: {abbr_count}, References: {ref_count})")
    print(f"Checks executed: {', '.join(m.CHECK_NAME for m in checks)}")
    print(f"Results saved to: {json_path}")
    return json_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 runner.py <file.tex | directory>")
        sys.exit(1)
    run(sys.argv[1])
