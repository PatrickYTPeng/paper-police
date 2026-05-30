#!/usr/bin/env python3
"""LaTeX Parser - Extract structured content from papers, skipping formulas and comments."""

import re
import sys
import json


def read_tex(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def remove_comments(text):
    """Remove LaTeX comments (lines starting with %), but preserve \\%."""
    return re.sub(r'(?<!\\)%.*', '', text)


def extract_title(text):
    m = re.search(r'\\title\{(.+?)\}', text, re.DOTALL)
    return m.group(1).strip() if m else ''


def extract_abstract(text):
    m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.DOTALL)
    return m.group(1).strip() if m else ''


def extract_keywords(text):
    m = re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', text, re.DOTALL)
    return m.group(1).strip() if m else ''


def extract_body(text):
    """Extract body text (from end of abstract to start of references)."""
    # Find end of abstract
    abs_end = re.search(r'\\end\{abstract\}', text)
    # Also skip keywords
    kw_end = re.search(r'\\end\{IEEEkeywords\}', text)
    start = 0
    if kw_end:
        start = kw_end.end()
    elif abs_end:
        start = abs_end.end()

    # Find start of references
    ref_start = re.search(r'\\begin\{thebibliography\}', text)
    end = ref_start.start() if ref_start else len(text)

    return text[start:end].strip()


def extract_references(text):
    """Extract all bibitem entries. Supports both standard \\bibitem{key} and
    natbib/bbl format \\bibitem[label]{key}."""
    refs = {}

    # Try standard format: \bibitem{key} content...
    pattern = r'\\bibitem(?:\[[^\]]*\])?\{(\w+)\}\s*(.*?)(?=\\bibitem|\s*\\end\{thebibliography\})'
    for m in re.finditer(pattern, text, re.DOTALL):
        key = m.group(1)
        content = m.group(2).strip()
        content_clean = _clean_ref_content(content)
        if content_clean:
            refs[key] = content_clean

    # If no refs found in main text, try to find and parse .bbl content
    # (bbl content may already be merged via \input)
    if not refs:
        # Look for natbib/biblatex bbl format
        bbl_pattern = r'\\bibitem\[([^\]]*)\]\{([^}]+)\}\s*(.*?)(?=\\bibitem|\s*\\end\{thebibliography\}|\Z)'
        for m in re.finditer(bbl_pattern, text, re.DOTALL):
            key = m.group(2)
            content = m.group(3).strip()
            content_clean = _clean_ref_content(content)
            if content_clean:
                refs[key] = content_clean

    return refs


def _clean_ref_content(content):
    """Clean LaTeX commands from reference content."""
    content = re.sub(r'\\newblock\s*', ' ', content)
    content = re.sub(r'\\textit\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\textbf\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\emph\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\url\{([^}]*)\}', r'\1', content)
    content = re.sub(r'\\href\{[^}]*\}\{([^}]*)\}', r'\1', content)
    content = re.sub(r'~', ' ', content)
    content = re.sub(r'\\&', '&', content)
    content = re.sub(r'\s+', ' ', content)
    return content.strip()


def strip_math(text):
    """Remove math formulas, leaving placeholders."""
    # Remove display math: \[ ... \], $$ ... $$, \begin{equation}...\end{equation}
    text = re.sub(r'\\\[.*?\\\]', ' [MATH] ', text, flags=re.DOTALL)
    text = re.sub(r'\$\$.*?\$\$', ' [MATH] ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}', ' [MATH] ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{align\*?\}.*?\\end\{align\*?\}', ' [MATH] ', text, flags=re.DOTALL)
    # Remove inline math: $ ... $
    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', ' [MATH] ', text)
    return text


def strip_environments(text):
    """Remove algorithm, table, and figure float environments, replacing with period to separate text."""
    # Algorithm environments
    text = re.sub(r'\\begin\{algorithm\}.*?\\end\{algorithm\}', '. ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{algorithmic\}.*?\\end\{algorithmic\}', '. ', text, flags=re.DOTALL)
    # Table environments
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '. ', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}', '. ', text, flags=re.DOTALL)
    # Figure environments
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '. ', text, flags=re.DOTALL)
    return text


def strip_latex_commands(text):
    """Remove common LaTeX commands, preserving plain text."""
    # Remove \cite{...}, keep markers for later checks
    text = re.sub(r'\\cite\{[^}]*\}', '[CITE]', text)
    # Remove \ref{...}, \eqref{...}, \label{...}
    text = re.sub(r'\\(?:eq)?ref\{[^}]*\}', '[REF]', text)
    text = re.sub(r'\\label\{[^}]*\}', '', text)
    # Remove \section, \subsection etc. but keep content
    text = re.sub(r'\\(?:sub)*section\*?\{([^}]*)\}', r'\1', text)
    # Remove \textit, \textbf but keep content
    text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
    # Remove \item
    text = re.sub(r'\\item', '', text)
    # Remove \begin{...}, \end{...}
    text = re.sub(r'\\(?:begin|end)\{[^}]*\}', '', text)
    # Remove other single commands like \noindent, \vspace, etc.
    text = re.sub(r'\\[a-zA-Z]+(?:\{[^}]*\}|\[[^\]]*\])*', '', text)
    # Clean extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def get_line_number(full_text, pos):
    """Get line number from character position."""
    return full_text[:pos].count('\n') + 1


def extract_cite_order(text):
    """Extract the order of \\cite appearances in the body."""
    body = extract_body(text)
    order = []
    for m in re.finditer(r'\\cite\{([^}]*)\}', body):
        keys = [k.strip() for k in m.group(1).split(',')]
        for k in keys:
            if k not in order:
                order.append(k)
    return order


def parse(filepath):
    raw = read_tex(filepath)
    text = remove_comments(raw)

    title = extract_title(text)
    abstract = extract_abstract(text)
    keywords = extract_keywords(text)
    body_raw = extract_body(text)
    refs = extract_references(text)
    cite_order = extract_cite_order(text)

    # Generate plain-text versions (for expression checks)
    body_plain = strip_latex_commands(strip_math(strip_environments(body_raw)))
    abstract_plain = strip_latex_commands(strip_math(abstract))

    return {
        'title': title,
        'abstract_raw': abstract,
        'abstract_plain': abstract_plain,
        'keywords': keywords,
        'body_raw': body_raw,
        'body_plain': body_plain,
        'references': refs,
        'cite_order': cite_order,
        'raw_text': raw,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 parse_tex.py <file.tex>")
        sys.exit(1)
    result = parse(sys.argv[1])
    # Output summary info
    print(f"Title: {result['title']}")
    print(f"Abstract length: {len(result['abstract_plain'])} chars")
    print(f"Body length: {len(result['body_plain'])} chars")
    print(f"Reference count: {len(result['references'])}")
    print(f"Citation order: {result['cite_order']}")
