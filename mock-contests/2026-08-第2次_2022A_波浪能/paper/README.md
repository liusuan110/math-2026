# Mac LaTeX 论文工作区

当前 `main.tex` 已完成问题一和问题二的阶段性写作。问题一包含动力学模型、数值方法、两张结果表、三张正式图和模型检验；问题二包含周期稳态平均功率口径、常量阻尼复频域优化、幂律阻尼周期射击优化、三张正式图、最优参数表和独立复核证据。

本稿件直接使用仓库中的 `templates/CUMCM2026-Complete-LaTeX/cumcmthesis.cls`，正文只引用 `../figures/final/` 中的论文正式图。

在本目录编译：

```bash
latexmk -xelatex main.tex
```

问题三开始后，继续在同一份 `main.tex` 中补全总体技术路线和后续问题；不要把稳定模型结果复制到其他目录。
