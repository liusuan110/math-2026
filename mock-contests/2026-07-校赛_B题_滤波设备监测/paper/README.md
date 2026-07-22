# Typst 论文入口

`main.typ` 来自仓库 `templates/cumcm-typst/template/论文骨架.typ`，已经改成 B 题四问结构。`lib.typ` 是模板的本地副本，`refs.bib` 维护论文参考文献。

`versions/` 保存已经对外确认过的里程碑 PDF；`main.pdf` 只表示当前源文件的最新本地预览，可以随时重新生成。

## 编译

在本题项目根目录执行：

```bash
typst compile --font-path paper/fonts paper/main.typ paper/main.pdf --root .
```

若 `paper/fonts/` 不存在，可从仓库根目录执行：

```bash
unzip -q -o templates/cumcm-typst/fonts.zip -d mock-contests/2026-07-校赛_B题_滤波设备监测/paper/fonts
```

字体和生成的 `main.pdf` 不纳入 Git。写作时遵循：每一问的最终数字都来自 `../data/results/`，每一张图都来自 `../figures/generated/`。电子版提交前把 `cover-display` 改为 `false`，并按 `../../提交checklist.md` 完成匿名、页数、PDF 体积和 MD5 检查。
