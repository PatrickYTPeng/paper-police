# PaperPolice

学术论文规范性检查工具 — Claude Code Skill

[English](README.md)

对英文学术论文（LaTeX）进行自动化规范性审查，结合规则引擎 + LLM 语感判断 + Google Scholar 频率验证，精准检测翻译腔、自造词、缩写不规范、参考文献问题。

## 检查维度

| 维度 | 检查内容 |
|------|---------|
| 表达规范 | 规则库匹配 + LLM 通读 + Scholar 频率验证 |
| 缩写规范 | 首次未定义、定义后仍用全称、摘要正文独立 |
| 参考文献 | 重复引用、引用顺序、格式一致性、摘要含引用、真实性验证 |

## 安装

项目级：
```bash
git clone https://github.com/PatrickYTPeng/paper-police.git .claude/skills/paper-police
```

全局：
```bash
git clone https://github.com/PatrickYTPeng/paper-police.git ~/.claude/skills/paper-police
```

## 使用

在 Claude Code 中：
```
/paper-police <.tex 文件或目录路径>
```

支持单文件和多文件项目目录。

## 输出

生成 HTML 报告：`{文件名}_PaperPolice_{日期时间}.html`
- 深色主题，三维度分组展示
- 有修改建议的问题：红绿 diff 对比（含前后句上下文）
- 仅有描述的问题：文字说明

查看报告后可回到 Claude Code 说"接受第 x 条修改"，自动执行。

## 目录结构

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

## 插拔式架构

每个检查是 `checks/` 下的独立文件。新增检查：加一个 .py 文件。删除检查：删文件即可。

## 适用场景

- 论文翻译后的规范性审查
- 投稿前 final check
- 研究生写作规范训练

## License

MIT
