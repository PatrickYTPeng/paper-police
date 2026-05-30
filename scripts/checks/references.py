#!/usr/bin/env python3
"""References compliance check.
1. Duplicate references
2. Citation order
3. Format consistency
4. Authenticity verification (handled by LLM WebSearch)
5. No citations in abstract
"""

import re
from difflib import SequenceMatcher

CHECK_ID = "REF"
CHECK_NAME = "References"


def check(parsed):
    """Execute references compliance check."""
    issues = []

    issues.extend(_check_abstract_citation(parsed))
    issues.extend(_check_duplicate(parsed))
    issues.extend(_check_order(parsed))
    issues.extend(_check_format_consistency(parsed))
    issues.extend(_check_authenticity(parsed))

    return issues


def _check_abstract_citation(parsed):
    """Check that abstract contains no citations."""
    issues = []
    abstract_raw = parsed['abstract_raw']
    cites = re.findall(r'\\cite\{[^}]*\}', abstract_raw)
    for cite in cites:
        issues.append({
            'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
            'description': f'Abstract should not contain citation {cite}. Abstract must be self-contained.',
        })
    return issues


def _check_duplicate(parsed):
    """Check for duplicate reference entries."""
    issues = []
    refs = parsed['references']
    keys = list(refs.keys())

    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            text_i = refs[keys[i]].lower()
            text_j = refs[keys[j]].lower()
            similarity = SequenceMatcher(None, text_i, text_j).ratio()
            if similarity > 0.75:
                issues.append({
                    'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
                    'description': (
                        f'References [{keys[i]}] and [{keys[j]}] have {similarity:.0%} similarity, possibly duplicated.\n'
                        f'[{keys[i]}]: {refs[keys[i]][:80]}...\n'
                        f'[{keys[j]}]: {refs[keys[j]][:80]}...\n'
                        f'Please verify and merge if they are the same paper.'
                    ),
                })
    return issues


def _check_order(parsed):
    """Check that citation numbers appear in ascending order of first occurrence."""
    issues = []
    cite_order = parsed['cite_order']

    def get_num(key):
        m = re.search(r'\d+', key)
        return int(m.group()) if m else 0

    nums = [get_num(k) for k in cite_order]
    max_seen = 0
    for i, n in enumerate(nums):
        if n < max_seen:
            issues.append({
                'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
                'description': (
                    f'Citation [{cite_order[i]}] (number {n}) appears before previously seen max number {max_seen}, '
                    f'violating first-occurrence ordering. Renumber references in order of first appearance.'
                ),
            })
        max_seen = max(max_seen, n)

    return issues


def _check_format_consistency(parsed):
    """Check reference format consistency."""
    issues = []
    refs = parsed['references']

    if len(refs) < 2:
        return issues

    has_pages = {}
    has_year = {}

    for key, text in refs.items():
        has_pages[key] = bool(re.search(r'pp?\.\s*\d+', text))
        has_year[key] = bool(re.search(r'(?:19|20)\d{2}', text))

    # Page number consistency
    with_pages = [k for k, v in has_pages.items() if v]
    without_pages = [k for k, v in has_pages.items() if not v]
    if with_pages and without_pages and len(without_pages) <= len(with_pages):
        issues.append({
            'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
            'description': (
                f'References [{", ".join(without_pages)}] missing page numbers, '
                f'while {len(with_pages)} others have them. Consider adding or unifying format.'
            ),
        })

    # Missing year
    without_year = [k for k, v in has_year.items() if not v]
    if without_year:
        issues.append({
            'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
            'description': f'References [{", ".join(without_year)}] missing publication year.',
        })

    return issues


def _check_authenticity(parsed):
    """Reference authenticity: output the reference list for LLM WebSearch verification.
    The script itself does not verify — this is handled by Claude in Step 5 of the skill workflow.
    It stores the reference data in the output for Claude to use.
    """
    # No issues output from script — verification is done by LLM
    return []
