# LabGuardian ICRCV 2026 Workspace

面向 ICRCV 2026 的论文工作区。**当前正式稿件是 IEEE 会议模板的 `main.tex`**（编译产物 `main.pdf`，6 页）。
`main.typ` 是早期 Typst 版本，仅作历史参考，不再维护。项目状态、会议日期与待办见 `HANDOFF.md`。

## 编译

模板类文件 `IEEEtran.cls` 已放在根目录（本机 TeX Live basic 不自带该类）：

```bash
pdflatex main.tex && pdflatex main.tex
```

参考文献直接写在 `main.tex` 的 `thebibliography` 中（本机无 `IEEEtran.bst`），无需 BibTeX；
`refs.bib` 保留为文献数据库，供后续需要时使用。

## 插图

正文插图统一来自 `figures/en/`，由脚本生成，保证稿件内不含中文标注：

```bash
python3 tools/make_figures.py
```

脚本从 `figures/cadx/*.pdf` 高分辨率栅格化并重排面板、改写英文标注；功率图从
`source-material/board_data/yolo_power_timeseries.csv` 与 `yolo_power_phases.json` 重绘；
Fig. 5 两栏都由 `source-material/board_run/inverting_amp_pipeline_result.json`（一次真实的完整链路运行）
生成：panel (a) 是照片叠加，panel (b) 是该运行 `netlist_v2` 的元件—网络图，两栏共用每网络配色。修改插图请改脚本后重新生成，不要手工编辑 `figures/en/`。

栅格化 `RASTER_DPI=800` 与保存 `SAVE_DPI=600` 不要调低：matplotlib 会把图像重采样到
`轴尺寸 × savefig dpi`，默认的 100 dpi 会让照片细节几乎全部丢失。

## 目录约定

- `main.tex` / `main.pdf`：论文正文与编译产物。
- `IEEEtran.cls`：会议模板类文件。
- `figures/en/`：论文实际引用的英文插图（脚本生成）。
- `figures/cadx/`、`figures/legacy-assets/`：项目原始插图（含中文标注），作为素材保留。
- `tools/make_figures.py`：插图生成脚本。
- `source-material/`：原始中文报告、源码归档、实验数据与旧绘图脚本。
- `conference-latex-template_10-17-19/`：会议官方模板原始包。
- `HANDOFF.md`：完整交接信息。

不要在论文中使用绝对 Windows 路径；新增资源请使用相对路径。
