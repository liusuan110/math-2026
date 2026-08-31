# Typst 论文入口

`main.typ` 来自仓库 `templates/cumcm-typst/template/论文骨架.typ`，已经改成 B 题四问结构。`lib.typ` 是模板的本地副本，`refs.bib` 维护论文参考文献。

`versions/` 保存已经对外确认过的里程碑 PDF；`main.pdf` 只表示当前源文件的最新本地预览，可以随时重新生成。

2026 年 AI 规范补正后，正文的“AI 工具使用声明”固定放在正文结尾、参考文献之前；独立支撑材料源文件位于 `supporting-materials/AI 工具使用详情.typ`，对应 PDF 的文件名必须保持为 `AI 工具使用详情.pdf`。第七版已在声明之后补入正式参考文献，四问核心代码分别保存在 `appendix-code/`，附录仅按带标题、边框和行号的代码清单格式载入，不放说明性段落。

## 编译

在本题项目根目录执行：

```bash
typst compile --font-path paper/fonts paper/main.typ paper/main.pdf --root .
typst compile --font-path paper/fonts 'paper/supporting-materials/AI 工具使用详情.typ' 'output/pdf/AI 工具使用详情.pdf' --root .
```

若 `paper/fonts/` 不存在，可从仓库根目录执行：

```bash
unzip -q -o templates/cumcm-typst/fonts.zip -d mock-contests/2026-07-校赛_B题_滤波设备监测/paper/fonts
```

字体和生成的 `main.pdf` 不纳入 Git。写作时遵循：每一问的最终数字都来自 `../data/results/`，每一张图都来自 `../figures/generated/`。当前 `cover-display` 已设为 `false`，生成的是不含承诺书和编号专用页的电子版；提交前按 `../../提交checklist.md` 完成匿名、页数、PDF 体积和 MD5 检查。
