# Mac LaTeX 论文工作区

当前 `main.tex` 已完成问题一的初步写作，内容包括摘要素材、问题重述、问题分析、模型假设、符号说明、动力学模型、数值方法、两张结果表、三张正式图、模型检验和问题一结论。

本稿件直接使用仓库中的 `templates/CUMCM2026-Complete-LaTeX/cumcmthesis.cls`，正文只引用 `../figures/final/` 中的论文正式图。

在本目录编译：

```bash
latexmk -xelatex main.tex
```

问题二开始后，继续在同一份 `main.tex` 中补全全文摘要、总体技术路线和后续问题；不要把稳定模型结果复制到其他目录。

