# LabGuardian ICRCV 2026 Workspace

这是面向 ICRCV 2026 的独立论文工作区。后续写作从根目录的 `main.typ` 开始；当前稿件见 `LabGuardian-ICRCV-2026-draft.pdf`，项目状态、会议日期和待办事项见 `HANDOFF.md`。

macOS 编译命令：

```bash
brew install typst
typst compile --root . main.typ LabGuardian-ICRCV-2026-draft.pdf
```

目录约定：

- `figures/`：论文插图。
- `source-material/`：原始报告、源码归档、实验数据和旧绘图脚本。
- `main.typ`：论文主文件。
- `refs.bib`：参考文献。
- `HANDOFF.md`：完整交接信息。

不要在主论文中使用绝对 Windows 路径；新增资源请使用相对路径。