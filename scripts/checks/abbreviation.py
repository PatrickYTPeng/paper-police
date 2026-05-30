#!/usr/bin/env python3
"""Abbreviation compliance check.
1. First occurrence without definition
2. Full name used after abbreviation has been defined (should use abbreviation)
3. Abstract and body checked independently
"""

import re

CHECK_ID = "ABBR"
CHECK_NAME = "Abbreviation"

# Minimal exemption list
MINIMAL_EXEMPT = {
    # Standards/organizations
    'IEEE', 'ISO', 'SI', 'ITU', 'ACM', 'AAAI', 'ICML', 'NeurIPS', 'ICLR',
    # Punctuation abbreviations
    'i.e.', 'e.g.', 'et al.', 'etc.', 'vs.',
    # Units
    'dB', 'dBm', 'Hz', 'kHz', 'MHz', 'GHz', 'THz',
    'km', 'cm', 'mm', 'nm', 'ms', 'ns', 'ps',
    'kW', 'mW', 'Mbps', 'Gbps', 'kbps',
    # CS universally known (no paper ever defines these)
    'API', 'APIs', 'GPU', 'GPUs', 'CPU', 'CPUs', 'TPU', 'TPUs',
    'URL', 'HTTP', 'HTTPS', 'JSON', 'XML', 'SQL', 'HTML', 'CSS',
    'RAM', 'ROM', 'USB', 'PDF', 'OS',
    'FLOPs', 'FLOP',
    # AI/ML universally known
    'AI', 'ML', 'DL', 'NLP', 'CV', 'RL', 'GAN', 'GANs',
    'VAE', 'MLP', 'CNN', 'RNN', 'LSTM', 'GRU',
    'LLM', 'LLMs', 'GPT', 'BERT', 'SFT', 'RLHF', 'PPO', 'DPO',
    'SOTA', 'IoT',
}

PSEUDO_CODE_KEYWORDS = {
    'IF', 'ELSE', 'ENDIF', 'FOR', 'ENDFOR', 'WHILE', 'ENDWHILE',
    'DO', 'DONE', 'THEN', 'END', 'RETURN', 'REQUIRE', 'ENSURE',
    'INPUT', 'OUTPUT', 'STATE', 'REPEAT', 'UNTIL', 'BREAK',
    'CONTINUE', 'FUNCTION', 'PROCEDURE', 'CALL', 'SET', 'LET',
    'TRUE', 'FALSE', 'NULL', 'NIL', 'AND', 'OR', 'NOT', 'TO',
}

ROMAN_NUMERALS = {
    'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
}

HYPHENATED_RE = re.compile(r'^[A-Z][a-z]+-[A-Z][a-z]+')
CAMEL_PRODUCT_RE = re.compile(r'^[A-Z][a-z]+[A-Z][a-z]+$')


def is_false_positive(word):
    if word in PSEUDO_CODE_KEYWORDS:
        return True
    if word in ROMAN_NUMERALS:
        return True
    if re.match(r'^[IVX]+-[A-Z]$', word):
        return True
    if HYPHENATED_RE.match(word):
        return True
    if CAMEL_PRODUCT_RE.match(word):
        return True
    return False


def extract_definitions(text):
    """Extract all abbreviation definitions, including sub-abbreviations from hyphenated compounds."""
    definition_pattern = r'\(([A-Za-z][A-Za-z0-9-]*[A-Z][A-Za-z0-9-]*)\)'
    defs = set()
    for m in re.finditer(definition_pattern, text):
        full = m.group(1)
        defs.add(full)
        if '-' in full:
            for part in full.split('-'):
                if len(part) >= 2 and any(c.isupper() for c in part):
                    defs.add(part)
    return defs


def extract_definitions_with_fullname(text):
    """Extract abbreviation definitions with their full names. Returns {ABBR: full_name} mapping.
    Matches "full name (ABBR)" pattern, validating full name accuracy via initial letter alignment.
    """
    # Match abbreviation in parentheses and up to 10 preceding words as candidate full name
    pattern = r'((?:[A-Za-z][-A-Za-z]*\s+){1,10})\(([A-Z][A-Za-z0-9-]*)\)'
    result = {}
    for m in re.finditer(pattern, text):
        candidate_words = m.group(1).strip().split()
        abbr = m.group(2)

        # Remove hyphens to get abbreviation letters (e.g., "A-BC" -> "ABC")
        abbr_letters = abbr.replace('-', '').upper()

        # From the end of candidate words, try to spell out the abbreviation using initial letters
        # Reverse matching: from last word backwards
        matched_words = []
        abbr_idx = len(abbr_letters) - 1
        for word in reversed(candidate_words):
            if abbr_idx < 0:
                break
            # Take the first letter of the word (ignoring articles/prepositions)
            first_letter = word[0].upper()
            if first_letter == abbr_letters[abbr_idx]:
                matched_words.insert(0, word)
                abbr_idx -= 1
            elif word.lower() in ('of', 'the', 'a', 'an', 'and', 'for', 'in', 'on', 'to', 'with', 'via', 'by'):
                # Articles/prepositions don't contribute to abbreviation letters but are part of the full name
                matched_words.insert(0, word)
            else:
                # First letter doesn't match and not a function word; try compound word (e.g., multiple-input -> MI)
                parts = word.split('-')
                if len(parts) > 1:
                    # Hyphenated compound: take initial letter of each part
                    initials = ''.join(p[0].upper() for p in parts if p)
                    # Check if multiple abbreviation letters can be matched
                    match_count = 0
                    for ch in reversed(initials):
                        if abbr_idx - match_count >= 0 and ch == abbr_letters[abbr_idx - match_count]:
                            match_count += 1
                        else:
                            break
                    if match_count > 0:
                        matched_words.insert(0, word)
                        abbr_idx -= match_count
                    else:
                        break
                else:
                    break

        # Verify all abbreviation letters were matched completely
        if abbr_idx < 0 and len(matched_words) >= 2:
            full_name = ' '.join(matched_words)
            result[abbr] = full_name

    return result


def find_first_occurrence(text, target):
    """Find the first occurrence of target in text, returning the sentence and surrounding context."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    pattern = re.compile(r'(?<![A-Za-z0-9-])' + re.escape(target) + r'(?![A-Za-z0-9])')
    for idx, sent in enumerate(sentences):
        m = pattern.search(sent)
        if m:
            prev_sent = sentences[idx-1].strip() if idx > 0 else ''
            next_sent = sentences[idx+1].strip() if idx < len(sentences)-1 else ''
            return {
                'prev_sent': prev_sent[:120],
                'current_sent': sent.strip()[:200],
                'next_sent': next_sent[:120],
            }
    return None


def make_issue(abbr, desc, text):
    """Generate an issue, automatically determining whether a diff can be shown."""
    ctx = find_first_occurrence(text, abbr)
    if ctx:
        modified = ctx['current_sent'].replace(abbr, f'full form ({abbr})', 1)
        if modified != ctx['current_sent']:
            return {
                'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'diff',
                'prev_sent': ctx['prev_sent'], 'current_sent': ctx['current_sent'],
                'next_sent': ctx['next_sent'], 'original': abbr,
                'replacement': f'full form ({abbr})',
                'modified_sent': modified,
                'description': desc,
            }
    return {
        'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'text',
        'description': desc + '\n(Note: this abbreviation may appear in a table or math environment and cannot be precisely located.)',
    }


def check(parsed):
    """Execute abbreviation compliance check."""
    issues = []
    abbrev_pattern = r'\b([A-Za-z]*[A-Z][A-Za-z]*[A-Z][A-Za-z]*)\b'
    compound_pattern = r'\b([A-Z][A-Za-z0-9]*(?:-[A-Z][A-Za-z0-9]*)+)\b'

    abstract_raw = parsed['abstract_raw']
    body_raw = parsed['body_raw']
    abstract_plain = parsed['abstract_plain']
    body_plain = parsed['body_plain']

    abstract_defs = extract_definitions(abstract_raw)
    body_defs = extract_definitions(body_raw)

    # === Sub-check 1&2: Compound abbreviations ===
    abstract_compounds = set(re.findall(compound_pattern, abstract_raw))
    body_compounds = set(re.findall(compound_pattern, body_raw))
    abstract_compound_parts = set()
    for comp in abstract_compounds:
        for part in comp.split('-'):
            if len(part) >= 2:
                abstract_compound_parts.add(part)
    body_compound_parts = set()
    for comp in body_compounds:
        for part in comp.split('-'):
            if len(part) >= 2:
                body_compound_parts.add(part)

    # Abstract compound abbreviations
    for comp in abstract_compounds:
        if comp in abstract_defs or comp in MINIMAL_EXEMPT or is_false_positive(comp):
            continue
        desc = f'Abbreviation "{comp}" used in abstract but not defined. Define it at first use: full form ({comp}).'
        issues.append(make_issue(comp, desc, abstract_plain))

    # Body compound abbreviations
    for comp in body_compounds:
        if comp in body_defs or comp in MINIMAL_EXEMPT or is_false_positive(comp):
            continue
        if comp in abstract_defs:
            desc = f'Abbreviation "{comp}" only defined in abstract. Redefine at first use in body (abstract and body are independent).'
        else:
            desc = f'Abbreviation "{comp}" used in body but never defined. Define it at first use: full form ({comp}).'
        issues.append(make_issue(comp, desc, body_plain))

    # === Sub-check 1&2: Individual abbreviations ===
    # Abstract
    abstract_abbrevs = set(re.findall(abbrev_pattern, abstract_raw))
    for abbr in abstract_abbrevs:
        if abbr in MINIMAL_EXEMPT or len(abbr) < 2:
            continue
        if is_false_positive(abbr):
            continue
        if abbr in abstract_defs:
            continue
        if abbr.endswith('s') and abbr[:-1] in abstract_defs:
            continue
        if abbr + 's' in abstract_defs:
            continue
        if abbr in abstract_compound_parts:
            continue
        desc = f'Abbreviation "{abbr}" used in abstract but not defined. Define it at first use: full form ({abbr}).'
        issues.append(make_issue(abbr, desc, abstract_plain))

    # Body
    body_abbrevs = set(re.findall(abbrev_pattern, body_raw))
    for abbr in body_abbrevs:
        if abbr in MINIMAL_EXEMPT or len(abbr) < 2:
            continue
        if is_false_positive(abbr):
            continue
        if abbr in body_defs:
            continue
        if abbr.endswith('s') and abbr[:-1] in body_defs:
            continue
        if abbr + 's' in body_defs:
            continue
        if abbr in body_compound_parts:
            continue
        if abbr in abstract_defs:
            desc = f'Abbreviation "{abbr}" only defined in abstract. Redefine at first use in body.'
        else:
            desc = f'Abbreviation "{abbr}" used in body but never defined. Define it at first use: full form ({abbr}).'
        issues.append(make_issue(abbr, desc, body_plain))

    # === Sub-check 3: Full name used after abbreviation defined ===
    # Find every occurrence where full name is used after definition (including plurals)
    body_defs_with_name = extract_definitions_with_fullname(body_raw)
    for abbr, full_name in body_defs_with_name.items():
        # Find definition position
        def_pattern = re.compile(re.escape(full_name) + r'\s*\(' + re.escape(abbr) + r'\)')
        def_match = def_pattern.search(body_raw)
        if not def_match:
            continue

        # Search for singular and plural forms of full name
        variants = [
            (full_name, abbr),              # singular
            (full_name + 's', abbr + 's'),  # plural +s
            (full_name + 'es', abbr + 's'), # plural +es
        ]
        # Skip unreasonable plurals
        if full_name.endswith('s') or full_name.endswith('x') or full_name.endswith('z'):
            variants = [(full_name, abbr)]

        for full_variant, abbr_variant in variants:
            # Exact word boundary matching
            fullname_re = re.compile(
                r'(?<![A-Za-z])' + re.escape(full_variant) + r'(?![A-Za-z])'
            )

            all_sents = re.split(r'(?<=[.!?])\s+', body_plain)
            found_def = False
            for gi, sent in enumerate(all_sents):
                # Skip definition sentence
                if not found_def:
                    if f'({abbr})' in sent or (full_name in sent and abbr in sent):
                        found_def = True
                    continue

                # Skip table/algorithm environment remnants
                if any(marker in sent for marker in ['[t]', '\\\\', ' & ', 'REQUIRE', 'ENSURE', 'STATE']):
                    continue

                # Check if sentence contains the variant
                if not fullname_re.search(sent):
                    continue
                if full_variant not in sent:
                    continue

                prev_s = all_sents[gi-1].strip() if gi > 0 else ''
                next_s = all_sents[gi+1].strip() if gi < len(all_sents)-1 else ''

                # Truncate display range to keep full name visible
                sent_display = sent.strip()
                if len(sent_display) > 200:
                    fn_pos = sent_display.find(full_variant)
                    start = max(0, fn_pos - 80)
                    end = min(len(sent_display), fn_pos + len(full_variant) + 80)
                    sent_display = ('...' if start > 0 else '') + sent_display[start:end] + ('...' if end < len(sent_display) else '')

                modified = sent_display.replace(full_variant, abbr_variant, 1)
                if modified == sent_display:
                    continue

                issues.append({
                    'id': CHECK_ID, 'name': CHECK_NAME, 'mode': 'diff',
                    'prev_sent': prev_s[:120],
                    'current_sent': sent_display,
                    'next_sent': next_s[:120],
                    'original': full_variant,
                    'replacement': abbr_variant,
                    'modified_sent': modified,
                    'description': f'Abbreviation "{abbr}" already defined. Use "{abbr_variant}" instead of full form "{full_variant}".',
                })

    return issues
