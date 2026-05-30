# PaperPolice

Academic writing compliance checker for LaTeX papers — Claude Code Skill.

[中文说明](README.zh-CN.md)

Automated compliance check for English academic papers combining rule-based detection + LLM judgment + Google Scholar frequency verification to catch translationese, coined terms, abbreviation issues, and reference problems.

## Check Dimensions

| Dimension | What It Checks |
|-----------|---------------|
| Expression | Rule-based matching + LLM read-through + Scholar frequency verification |
| Abbreviation | Undefined at first use, full form after definition, abstract/body independence |
| References | Duplicates, citation order, format consistency, abstract citations, authenticity |

## Installation

Project-level:
```bash
git clone https://github.com/PatrickYTPeng/paper-police.git .claude/skills/paper-police
```

Global:
```bash
git clone https://github.com/PatrickYTPeng/paper-police.git ~/.claude/skills/paper-police
```

## Usage

In Claude Code:
```
/paper-police <path to .tex file or directory>
```

Supports single .tex files and multi-file project directories.

## Output

Generates an HTML report: `{filename}_PaperPolice_{datetime}.html`
- Dark theme, grouped by dimension
- Issues with fix suggestions: red/green diff with surrounding context
- Issues with description only: text explanation

After reviewing the report, tell Claude Code "accept issue #x" to apply fixes automatically.

## Structure

```
paper-police/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   ├── runner.py
│   ├── parse_tex.py
│   ├── gen_report.py
│   └── checks/
│       ├── expression.py
│       ├── abbreviation.py
│       └── references.py
└── assets/
    └── informal_rules.json
```

## Pluggable Architecture

Each check is an independent file under `checks/`. Add a file to add a check. Delete a file to remove one.

## Use Cases

- Post-translation compliance review
- Pre-submission final check
- Writing training for graduate students

## License

MIT
