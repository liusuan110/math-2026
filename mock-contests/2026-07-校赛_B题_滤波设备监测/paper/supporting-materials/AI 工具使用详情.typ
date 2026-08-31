#set document(
  title: "AI 工具使用详情",
  author: "2026 校赛 B 题参赛队",
)

#let song = ("SimSun", "Songti SC")
#let hei = ("SimHei", "Heiti SC")

#set page(
  paper: "a4",
  margin: (top: 2.1cm, bottom: 2.0cm, left: 2.2cm, right: 2.2cm),
  header: context [
    #set text(font: song, size: 8.5pt, fill: black)
    #if counter(page).get().first() > 1 [2026 校赛 B 题 · AI 工具使用详情]
  ],
  footer: context [
    #set text(font: song, size: 8.5pt, fill: black)
    #align(center)[第 #counter(page).display("1") 页]
  ],
)
#set text(font: ("Times New Roman", ..song), size: 10.5pt, lang: "zh", region: "cn")
#set par(justify: true, first-line-indent: 2em, leading: 0.72em)
#set heading(numbering: none)
#show heading.where(level: 1): it => {
  v(0.8em)
  block(width: 100%, inset: (top: 0.3em, bottom: 0.3em), stroke: (bottom: 0.8pt + black))[
    #set text(font: hei, size: 14pt, fill: black)
    #align(center)[#it.body]
  ]
  v(0.35em)
}
#show heading.where(level: 2): it => {
  v(0.55em)
  set text(font: hei, size: 11.5pt, fill: black)
  it.body
  v(0.15em)
}
#show strong: set text(font: hei)

#align(center)[
  #set text(font: hei, fill: black)
  #text(size: 19pt)[AI 工具使用详情]
  #v(0.45em)
  #text(size: 12pt, fill: black)[2026 校赛 B 题：滤波设备监测与维护决策]
]

#v(1em)
#grid(
  columns: (2.4cm, 1fr),
  column-gutter: 0.5cm,
  row-gutter: 0.4em,
  [*作品名称*], [滤波设备性能退化建模与维护策略优化],
  [*题号*], [B 题],
  [*使用时间*], [2026 年 7 月 22 日（建模、程序与论文阶段）；2026 年 8 月 30 日（AI 规范补正阶段）],
  [*详情文件*], [AI 工具使用详情.pdf],
)

#v(0.8em)
#block[
  #set par(first-line-indent: 0em)
  *透明性说明：*本文件依据当时的 Codex 会话记录、项目源文件、测试与编译记录补写。AI 参与程度较深，包括建模方案辅助设计、程序初稿与论文初稿；本文件不将这些内容简化表述为“仅语言润色”。原作品完成于规定试行日之前；本次按 2026 年 9 月 1 日起试行的新规定提前补正。
]

= 一、所用 AI 工具名称、版本或型号

#table(
  columns: (1.2fr, 1.25fr, 1.55fr),
  inset: 6pt,
  stroke: none,
  table.hline(stroke: 0.9pt + black),
  table.header([*工具*], [*版本/型号*], [*用途阶段*]),
  table.hline(stroke: 0.5pt + black),
  [OpenAI Codex 桌面版], [核心模型：`gpt-5.6-sol`], [题目与数据分析、建模、编程、调试、论文起草与排版、合规补正],
  [Codex 客户端], [`0.145.0-alpha.27`], [2026-07-22 主要建模与写作会话],
  [Codex 客户端], [`0.151.0-alpha.7.1`], [2026-08-30 规范核对、声明与详情补正],
  table.hline(stroke: 0.9pt + black),
)

版本信息来自对应会话的本地记录。项目文件与会话记录中未发现本题使用其他生成式 AI 工具的证据。Python、Typst 及其数值计算库属于程序运行和排版工具，不在上表中作为 AI 工具重复列示。

#pagebreak()
= 二、具体使用目的和环节

#table(
  columns: (0.55fr, 1.35fr, 2.4fr),
  inset: 6pt,
  stroke: none,
  table.hline(stroke: 0.9pt + black),
  table.header([*环节*], [*AI 具体作用*], [*形成的主要内容*]),
  table.hline(stroke: 0.5pt + black),
  [前期], [读取题目、附件和既有仓库，辅助拆分四问], [数据字典、建模路线、统一工作区和可复现流水线骨架],
  [问题一], [辅助设计并实现日级聚合、季节-趋势-维护周期分解与事件研究], [设备固定效应、Fourier/月份稳健性、设备簇自助区间、异常日标记],
  [问题二], [辅助设计并实现分层退化状态和寿命联合判据], [90/180/270 日时间留出、结构敏感性、2,000 路径/设备的寿命情景模拟],
  [问题三], [辅助设计并实现维护类型响应、规则枚举和稳健性复验], [129 组周期/状态触发规则、逐设备与全厂统一策略、损伤情景和独立种子检验],
  [问题四], [辅助设计并实现路径成本线性拆分、价格网格和后悔值分析], [共同价格、分项维护价格、单因素扫描及最小最大后悔方案],
  [论文], [起草和反复修订 Typst 正文，生成图表并协助检查排版], [摘要、四问方法与结果、灵敏度、局限性、附录代码入口],
  [合规], [读取 2026 年试行规定，补入正文声明并编制本详情], [声明位置、规定用语、工具型号、用途、交互方式及人工核验说明],
  table.hline(stroke: 0.9pt + black),
)

= 三、主要提示方式与使用过程说明

== 3.1 提示方式

参赛队以中文自然语言提出阶段性目标，由 Codex 在获授权的本地工作区内读取文件、编辑代码、运行程序并返回中间证据。提示主要是“目标+约束+验收”形式，而非一次要求直接生成终稿。

== 3.2 典型交互示例（依原意摘录）

#enum(
  [“使用我的 `math-2026` 仓库里的模板和算法规划这道题，先开始完成题目前的分析。”],
  [“开始在当前工作区建立本题基本骨架，改用仓库中的 Typst 模板。”],
  [“开始问题一正式建模”、“实现问题二”、“开始规划问题三”、“实现问题四”；每个阶段后要求总结当前进度。],
  [“严格按照 2026 年试行规定，完整补正论文中声明位置和 AI 工具使用详情。”],
)

== 3.3 使用过程

#enum(
  [*Codex 先读取当前文件与数据结构。*题目、两份附件、仓库模板和既有算法被作为输入；原始附件保留在只读数据区。],
  [*Codex 生成或修订源码与文稿。*主要产物为 Python 模块、测试、结果表、图像、决策记录与 Typst 论文。],
  [*Codex 运行检查并根据证据修正。*包括数据完整性审计、模型时间留出、数值敏感性、单元测试、Typst 编译和 PDF 逐页渲染。],
  [*参赛队分阶段决定继续、换模板或进入下一问。*占位接口与中间结果未全部纳入终稿。],
)

= 四、AI 输出的采纳、人工修改和核验情况

== 4.1 采纳与修改

#table(
  columns: (1.0fr, 1.7fr, 2.25fr),
  inset: 6pt,
  stroke: none,
  table.hline(stroke: 0.9pt + black),
  table.header([*处理类型*], [*具体情况*], [*依据或结果*]),
  table.hline(stroke: 0.5pt + black),
  [采纳], [采纳 AI 辅助生成的主代码框架、大部分模型实现、结果图表和论文初稿], [最终形成 `q1_analysis.py`至`q4_sensitivity.py`、`data/results/`、`figures/generated/`和`paper/main.typ`],
  [人工指向修改], [参赛队决定使用自有仓库、迁移到统一工作区、改用 Typst，并按问题一至四分阶段继续], [项目结构、模板与实施顺序均随这些指令调整],
  [未采纳/替换], [早期 LaTeX 入口被 Typst 替换；问题二至四的初期占位接口未当作正式结果；模板内演示性虚构文献被移除], [终稿只保留由流水线产生的正式数字和实际使用的 Typst 入口],
  [表述修正], [对长期外推、维护指征偏差、小样本大维护、未观测真实失效等限制保留谨慎表述], [论文不把场景外推包装为已校准的统计事实，并单列模型缺点与改进],
  table.hline(stroke: 0.9pt + black),
)

== 4.2 主要核验情况

#enum(
  [*数据核验：*识别 10 台设备、114,977 条带时间戳监测记录和 127 条维护记录；127 个维护事件均对齐到设备日序列。],
  [*模型核验：*问题一比较 Fourier 与月份季节规格；问题二采用 90/180/270 日时间留出、留一设备与 9 组结构情景；问题三使用公共随机数搜索并换独立种子复验；问题四固定物理路径后重定价。],
  [*程序核验：*2026-07-22 项目记录显示 19 项自动测试全部通过；2026-08-30 补正时再次运行同一测试集。],
  [*论文核验：*每一问数字从 `data/results/` 回填，图像从 `figures/generated/` 引用；Typst 编译后把全文渲染为页面图像，检查断页、字体、图表、声明位置和页码。],
)

== 4.3 人工责任与局限

本题的 AI 输出不是可以免复核的权威结论。尤其是寿命区间主要反映当前结构、参数和残差扰动情景，不是有真实失效样本校准过的覆盖率承诺；维护策略也依赖两年观测、少量大维护记录和预设损伤情景。参赛队对最终提交内容、数字与竞赛合规性承担责任。

#v(0.7em)
#line(length: 100%, stroke: 0.5pt + black)
#v(0.8em)
#align(right)[
  #set text(size: 9pt, fill: black)
  记录整理日期：2026 年 8 月 30 日
]
