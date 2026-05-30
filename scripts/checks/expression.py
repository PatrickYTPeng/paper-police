#!/usr/bin/env python3
"""Expression compliance check - rule-based matching subprocess.
Detects informal, translationese, and redundant expressions.
LLM read-through + Scholar verification is handled by Claude in the skill workflow.
"""

import re
import os
import json

CHECK_ID = "EXPR"
CHECK_NAME = "Expression"


def check(parsed):
    """Check for informal expressions, return issue list."""
    issues = []

    rules_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'assets', 'informal_rules.json'
    )
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules_data = json.load(f)

    rules = rules_data['rules']
    full_text = parsed['body_plain']
    abstract_text = parsed['abstract_plain']
    all_text = abstract_text + '\n\n' + full_text

    # Split by sentences
    sentences = re.split(r'(?<=[.!?])\s+', all_text)

    for rule in rules:
        pattern = rule['pattern']
        if ' ' in pattern:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)
        else:
            regex = re.compile(r'\b' + re.escape(pattern) + r'\b', re.IGNORECASE)

        for m in regex.finditer(all_text):
            # Skip near [MATH] or [CITE]
            nearby = all_text[max(0, m.start()-10):m.end()+10]
            if '[MATH]' in nearby or '[CITE]' in nearby:
                continue

            # Locate sentence + surrounding context
            pos = m.start()
            current_sent = ''
            prev_sent = ''
            next_sent = ''
            char_count = 0
            for idx, sent in enumerate(sentences):
                if char_count <= pos < char_count + len(sent) + 1:
                    current_sent = sent.strip()
                    prev_sent = sentences[idx-1].strip() if idx > 0 else ''
                    next_sent = sentences[idx+1].strip() if idx < len(sentences)-1 else ''
                    break
                char_count += len(sent) + 1

            matched_text = m.group()
            replacement = rule['replacement'].split('/')[0].strip()
            modified_context = current_sent.replace(matched_text, replacement, 1)

            issues.append({
                'id': CHECK_ID,
                'name': CHECK_NAME,
                'mode': 'diff',
                'prev_sent': prev_sent[:120],
                'current_sent': current_sent[:200],
                'next_sent': next_sent[:120],
                'original': matched_text,
                'replacement': replacement,
                'modified_sent': modified_context[:200],
                'description': f'"{matched_text}" — {rule["note"]}. Suggested replacement: {rule["replacement"]}',
            })

    return issues
