---
name: "paper-police"
description: "Academic writing compliance check. Triggers: 'check paper', 'review paper', 'paper police', 'PaperPolice'"
allowed-tools: [Bash, Read, Write, Glob, Grep, WebSearch, WebFetch]
user-invocable: true
disable-model-invocation: false
---

# PaperPolice - Academic Writing Compliance Check

Automated compliance check for English academic papers (LaTeX .tex), covering expression, abbreviation, and references.

## Usage
```
/paper-police <path to .tex file or directory>
```

Supports single .tex files and multi-file project directories.

## Workflow

### Step 1: File Validation
Verify input is a .tex file or a directory containing .tex files. Stop if invalid.

### Step 2: Automated Checks
Run `python3 scripts/runner.py <path>` to execute three dimensions of checks:

| Dimension | Checks |
|-----------|--------|
| Expression | Rule-based matching for informal/translationese/redundant expressions |
| Abbreviation | Undefined at first use; full form used after definition; abstract/body independence |
| References | Duplicates; citation order; format consistency; no citations in abstract |

### Step 3: Abbreviation LLM Filtering
Review ALL abbreviation results from Step 2. For each flagged abbreviation:
1. Determine if it is a universally recognized term in the paper's field that does not need definition.
2. Determine if it is a tool name, dataset name, or model name (not a true abbreviation).
3. Only exempt abbreviations that any reader in the field would immediately recognize without definition.
4. Remove exempted items from the issues list. Keep all others.

### Step 4: Expression LLM Review
This step is MANDATORY and must be thorough. Do NOT skip or abbreviate.

1. Read the ENTIRE body_plain text paragraph by paragraph (not just the first few paragraphs).
2. For each paragraph, identify ALL expressions that appear to be:
   - Translationese (literal translations from another language)
   - Coined compound terms rarely seen in academic literature
   - Informal or colloquial phrasing
   - Awkward collocations that a native speaker would not use
3. Compile a complete list of ALL suspicious expressions found across the entire paper.
4. For EACH expression in the list, use WebSearch to query Google Scholar with the exact phrase in quotes. Check the result count.
5. If a phrase returns fewer than ~100 results on Scholar, mark it as an issue with a suggested replacement.
6. Append ALL confirmed low-frequency expressions to the issues JSON as EXPR items with diff context.

Do NOT stop after finding 2-3 issues. The entire paper must be reviewed end-to-end.

### Step 5: Reference Authenticity Verification
This step is MANDATORY. Every single reference must be verified.

1. Extract ALL references from the paper (from bibitem or bbl format).
2. For EACH reference entry, use WebSearch to search for the paper title.
3. If the paper cannot be found via search (no matching results), flag it as a potentially fabricated reference.
4. For references that are found, briefly verify that the authors and venue match.
5. Report any references that appear non-existent or have mismatched metadata.

Do NOT skip any references. Do NOT sample or spot-check. Verify every single one.

### Step 6: Generate HTML Report
Run `python3 scripts/gen_report.py <issues.json>` to generate the report.
Naming: `{filename}_PaperPolice_{YYYYMMDD_HHMM}.html`

### Step 7: Guide User Modifications
Inform user of the report path. User can reply "accept issue #x" and Claude will execute the Edit.

## Dimension Details

### Expression (EXPR)
- Rule-based matching: 103 informal expression rules with replacement suggestions
- LLM review: identify suspicious expressions by reading, verify via Scholar

### Abbreviation (ABBR)
- Abstract and body checked independently
- First occurrence must include full form + abbreviation in parentheses
- After definition, subsequent occurrences should use abbreviation (including plural forms)
- Compound abbreviations treated as whole units
- Minimal exemption list + LLM field-specific judgment

### References (REF)
- Duplicate detection (title similarity > 75%)
- Citation numbers must appear in ascending order of first occurrence
- Format consistency (page numbers, year present across all entries)
- Abstract must not contain citations
- Authenticity verification (LLM WebSearch)
