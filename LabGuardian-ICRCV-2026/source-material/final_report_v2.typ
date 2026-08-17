#import "@preview/fletcher:0.5.7" as fletcher: diagram, edge, node
// ============================================================================
//  英特尔杯大学生电子设计竞赛嵌入式系统专题邀请赛 —— 作品设计报告 (Final Report)
//  Typst 模板（严格按照官方《中文报告模板》排版要求转写）
// ----------------------------------------------------------------------------
//  排版要求一览（与官方模板批注逐条对应）：
//   · 报告题目（页眉右侧）         小五号黑体
//   · 中文题目                     三号黑体居中，上下各空一行
//   · "摘要" 二字                  四号黑体居中
//   · 摘要正文                     五号宋体，首行缩进二字，单倍行距
//   · 中文关键词标签               小四号黑体；关键词五号宋体，逗号分开，末尾无标点
//   · 英文题目                     三号 Times New Roman 居中加黑，一律大写，上下各空一行
//   · "ABSTRACT"                   四号 Times New Roman 居中加黑
//   · 英文摘要正文                 五号 Times New Roman，首行缩进两格，单倍行距
//   · "Key words" 标签             小四 Times New Roman 加黑（Key words 间加空格）
//   · 目录标题 "目 录"             三号黑体居中，上下各空一行；条目五号宋体单倍行距
//   · 一级标题（第X章）            三号黑体居中，上下各空一行
//   · 二级标题（X.Y）              四号黑体，序数空两格，单倍行距
//   · 三、四级标题（X.Y.Z）        小四宋体，空两格书写序数
//   · 正文                         中文五号宋体 / 英文五号 Times New Roman，首行缩进二字，单倍行距
//   · 分项序号                     (1)、(2)、(3) …
//   · 参考文献标注                 中括号 + 上标形式
//   · 公式                         另起一行，圆括号编号(章-序)，转行在等号/运算符处，等号对齐
//   · 表格                         三线表；表题在表上方居中，五号宋体加黑，"表X-Y 标题"无尾点
//   · 插图                         图序图题在图下方居中，五号宋体加黑，"图X-Y 标题"
//   · 页脚                         第 X 页  共 N 页（正文从第 1 页起编号）
//
//  编译： typst compile report_template.typ
//  预览： typst watch   report_template.typ
//  字体： Windows 自带 SimSun / SimHei / KaiTi / Times New Roman（已配 macOS 回退）
// ============================================================================


// ─────────────────────────── ① 可填写信息 ────────────────────────────────
// 把下面的内容替换为你自己的报告信息即可。
// 【封面信息：题目/姓名/导师/学校 待最后填写——当前为工作占位】
#let 竞赛年份 = "2026"
#let 报告题目 = "LabGuardian：基于边缘AI的智能助教系统"
#let 英文题目 = "LABGUARDIAN: AN INTELLIGENT TEACHING ASSISTANT SYSTEM BASED ON EDGE AI"
#let 学生姓名 = "张芯然 刘稣安 阮佳丽"
#let 指导教师 = "程琨"
#let 参赛学校 = "北京邮电大学"

#let 中文摘要 = [
  高校电子实验中，学生常出现“原理图正确但实物接错”的接线错误。这类错误难以从外观直接发现，排查依赖教师逐项检查，而电子实验课师生比偏高，教师难以及时照顾全部学生。本文研究面向电子实验教学的自动接线诊断与解释方法，目标是在不依赖云端、可在边缘设备本地运行的前提下，给出可审计、可解释的诊断结果。所提系统 LabGuardian 不让大模型直接判定电路对错，而是把感知与判断分开。系统以面包板俯视照片为输入，先用自建引脚级数据集训练的关键点模型检测引脚，再将引脚对齐到孔位并结合面包板导通规则，重构出引脚级电气网表；随后由确定性图比对算法判断对错，输出带证据引用的结构化错误码；最后由端侧小模型在固定诊断证据范围内生成教学解释，并由证据一致性校验拦截无依据扩展。教学解释模型通过学习双教师模型在固定证据下生成的回答得到，再经 INT4 量化后部署到边缘端。其中，引脚级电气网表重构、判断与解释的分工设计，以及面向边缘部署的教学解释模型训练与部署，是本文的主要工作。系统在 Intel DK-2500 上以 8 GB 内存预算完成视觉识别与端侧解释，能够满足课堂现场使用。
]
#let 中文关键词 = ("面包板接线诊断", "神经—符号", "可审计解释", "知识蒸馏", "边缘部署")

#let 英文摘要 = [
  In undergraduate electronics laboratories, students often build circuits that are schematically correct but physically miswired. Such errors are hard to spot from appearance and must be checked item by item, while the high student-to-teacher ratio makes timely help difficult. This paper studies automatic diagnosis and explanation of breadboard wiring for laboratory teaching, aiming to produce auditable and explainable feedback that runs locally on an edge device without cloud access. The proposed system, LabGuardian, does not let a large model judge circuit correctness directly; instead it separates perception from judgement. It takes a top-view breadboard photo, detects pin keypoints with a model trained on a self-built pin-level dataset, aligns each pin to its hole and reconstructs a pin-level electrical netlist using breadboard connectivity rules; a deterministic graph-matching engine then decides correctness and emits structured error codes with evidence references; finally an on-device small model generates teaching explanations under fixed diagnostic evidence, while an evidence-consistency check rejects unsupported additions. The teaching-explanation model is trained on teacher responses generated under the same fixed evidence and then quantized to INT4 for edge deployment. The main work consists of keypoint-based pin-level netlist reconstruction, the division of labour between deterministic judgement and evidence-constrained explanation, and training a small teaching model for on-device deployment. On the Intel DK-2500, the system performs visual recognition and on-device explanation within an 8 GB memory budget for classroom use.
]
#let 英文关键词 = (
  "breadboard wiring diagnosis",
  "neuro-symbolic",
  "auditable explanation",
  "knowledge distillation",
  "edge intelligence",
)


// ─────────────────────────── ② 字体与字号 ────────────────────────────────
#let 正文字体 = ("Times New Roman", "SimSun", "Songti SC", "Source Han Serif SC")   // 宋体 / 英文 Times
#let 标题字体 = ("Times New Roman", "SimHei", "Heiti SC", "Noto Sans SC")           // 黑体
#let 楷体字体 = ("KaiTi", "STKaiti", "Kaiti SC")                                    // 楷体
#let 华文楷体 = ("STKaiti", "华文楷体", "Kaiti SC")                                  // 华文楷体（封面“作品设计报告”）
#let 楷体GB = ("KaiTi_GB2312", "楷体_GB2312", "KaiTi", "STKaiti", "Kaiti SC")      // 楷体_GB2312（封面题目/信息栏；Windows 无此字体时回退 KaiTi）
#let 英文字体 = ("Times New Roman", "STSong")

#let 小五 = 9pt
#let 五号 = 10.5pt
#let 小四 = 12pt
#let 四号 = 14pt
#let 三号 = 16pt
#let 二号 = 22pt
#let 小二 = 18pt
#let 小初 = 36pt
#let 一行 = 16pt    // “空一行” 的近似高度（约一行正文）


// ─────────────────────────── ③ 页面：页眉 / 页脚 ─────────────────────────
// 页眉：左侧 ESDC 徽标 + 右侧报告题目（小五黑体）+ 下方分隔线，全篇可见。
#let 页眉 = {
  set text(font: 标题字体, size: 小五)
  set par(leading: 0pt, spacing: 0pt)
  // 分隔线作为 block 的底边框，始终紧贴徽标/题目底部（避免内容与线之间出现空隙）
  // 左：完整 ESDC 徽标（含下方文字）；右：报告题目，与徽标底部对齐
  block(width: 100%, stroke: (bottom: 0.7pt), inset: (bottom: 3pt))[
    #grid(
      columns: (auto, 1fr),
      align: (left + bottom, right + bottom),
      image("assets/esdc_logo.jpg", height: 1.2cm), text(font: 标题字体, size: 小五)[#报告题目],
    )
  ]
}

// 页脚：第 X 页 共 N 页（仅正文启用；正文从第 1 页起算）
#let 页脚 = context {
  set align(center)
  set text(font: 正文字体, size: 五号)
  [第 #counter(page).display() 页　共 #counter(page).final().first() 页]
}

#set page(
  paper: "a4",
  margin: (top: 2.54cm, bottom: 2.54cm, left: 3cm, right: 3cm),
  header: 页眉,
  header-ascent: 9pt, // 分隔线落在约 2.78cm 处、logo 顶在约 1.5cm 处，与原模板一致
  footer: none, // 前置部分（封面～目录）不显示页码，正文处再开启
)


// ─────────────────────────── ④ 正文与段落 ────────────────────────────────
#set text(font: 正文字体, size: 五号, lang: "zh", region: "cn")
// 首行缩进二字（all:true 使每段含标题后首段均缩进）；单倍行距
#set par(first-line-indent: (amount: 2em, all: true), leading: 1em, spacing: 1em, justify: true)
#set underline(offset: 3pt)


// ─────────────────────────── ⑤ 标题编号与样式 ────────────────────────────
// 一级用中文“第X章”，其余用 X.Y / X.Y.Z 数字编号
#set heading(numbering: (..nums) => {
  let n = nums.pos()
  if n.len() == 1 {
    "第" + ("〇", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十").at(n.first()) + "章"
  } else {
    numbering("1.1.1.1", ..n)
  }
})

// 一级标题：三号黑体居中，上下各空一行；每章另起一页并复位图/表/公式计数器
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  counter(math.equation).update(0)
  counter(figure.where(kind: image)).update(0)
  counter(figure.where(kind: table)).update(0)
  set align(center)
  set par(first-line-indent: (amount: 0em, all: false))
  v(一行)
  text(font: 标题字体, size: 三号, weight: "bold")[
    #if it.numbering != none { counter(heading).display() + "  " }
    #it.body
  ]
  v(一行)
}

// 二级标题：四号黑体，序数空两格（缩进两字），单倍行距
#show heading.where(level: 2): it => {
  set par(first-line-indent: (amount: 0em, all: false))
  v(0.6em)
  text(font: 标题字体, size: 四号, weight: "bold")[
    #h(2em)#counter(heading).display()#h(0.5em)#it.body
  ]
  v(0.3em)
}

// 三级 / 四级标题：小四宋体，空两格书写序数
#show heading.where(level: 3): it => {
  set par(first-line-indent: (amount: 0em, all: false))
  v(0.4em)
  text(font: 正文字体, size: 小四, weight: "bold")[
    #h(2em)#counter(heading).display()#h(0.5em)#it.body
  ]
  v(0.2em)
}
#show heading.where(level: 4): it => {
  set par(first-line-indent: (amount: 0em, all: false))
  v(0.3em)
  text(font: 正文字体, size: 小四, weight: "bold")[
    #h(2em)#counter(heading).display()#h(0.5em)#it.body
  ]
  v(0.2em)
}


// ─────────────────────────── ⑥ 图 / 表 / 公式编号 ────────────────────────
// 编号按章重置：图X-Y / 表X-Y / (X-Y)
#set figure(numbering: num => context [#counter(heading).get().first()\-#num])
#set math.equation(numbering: num => context [(#counter(heading).get().first()\-#num)])
#show figure.where(kind: image): set figure(supplement: [图])
#show figure.where(kind: table): set figure(supplement: [表])
#show figure.where(kind: table): set figure.caption(position: top)   // 表题在上方
#show figure.where(kind: image): set figure.caption(position: bottom) // 图题在下方

// 图/表标题：五号宋体加黑，"表2-1 标题"（序号与“表/图”之间不加点，标题前空一格，末尾无标点）
#show figure.caption: it => context {
  set text(font: 正文字体, size: 五号)
  set par(first-line-indent: (amount: 0em, all: false), leading: 0.7em)
  align(center)[#text(weight: "bold")[#it.supplement#it.counter.display(it.numbering)]#h(0.5em)#it.body]
}
// 公式占位居中、编号右对齐由 Typst 自动处理
#set math.equation(supplement: none)


// ─────────────────────────── ⑦ 实用宏 ───────────────────────────────────
// 参考文献上标标注：正文中写 #cite(<spice>) 得到上标 [1]

// 三线表：顶线 1pt + 表头底线 0.5pt + 底线 1pt，无竖线
#let 三线表(columns: (), align-cells: auto, header: (), rows: ()) = {
  let n = rows.len()
  set text(size: 小五)
  table(
    columns: columns,
    align: align-cells,
    inset: (x: 5pt, y: 4pt),
    stroke: (x, y) => {
      if y == 0 { (top: 1pt, bottom: 0.5pt) } else if y == n { (bottom: 1pt) } else { none }
    },
    table.header(..header.map(c => [*#c*])),
    ..rows.flatten().map(c => [#c]),
  )
}

// 中文关键词行
#let 关键词行(..kw) = {
  set par(first-line-indent: (amount: 0em, all: false), leading: 1em)
  text(font: 标题字体, size: 小四, weight: "bold")[关键词：]
  text(font: 正文字体, size: 五号)[#kw.pos().join("，")]
}
// 英文关键词行
#let key-words-line(..kw) = {
  set par(first-line-indent: (amount: 0em, all: false), leading: 1em)
  text(font: 英文字体, size: 小四, weight: "bold")[Key words: ]
  text(font: 英文字体, size: 五号)[#kw.pos().join(", ")]
}


// ── 架构图 / 流程图绘制辅助（纯黑白：黑描边+白底，层次以实线/虚线区分）──
#let fig-ink = black
#let fig-aux = black
#let fig-plain = "plain"
#let fig-emph = "emph"
#let fig-warm = "warm"
#let box-stroke(style) = if style == "warm" {
  (paint: fig-ink, thickness: 0.7pt, dash: "dashed")
} else { 0.7pt + fig-ink }

#let arch-layer(name, modules, fill: fig-plain) = block(
  width: 100%,
  fill: white,
  stroke: box-stroke(fill),
  radius: 3pt,
  inset: (x: 9pt, y: 8pt),
  grid(
    columns: (7.5em, 1fr),
    column-gutter: 11pt,
    align: (center + horizon, left + horizon),
    text(weight: "bold", size: 10pt, fill: fig-ink, name),
    {
      set par(leading: 0.62em, justify: false, first-line-indent: 0pt)
      text(size: 8.4pt, fill: fig-ink, modules)
    },
  ),
)
#let flow-node(body, fill: fig-plain) = block(
  width: 100%,
  fill: white,
  stroke: box-stroke(fill),
  radius: 3pt,
  inset: (x: 10pt, y: 8pt),
  align(center + horizon, {
    set par(leading: 0.62em, justify: false, first-line-indent: 0pt)
    text(size: 9pt, body)
  }),
)
#let v-both = align(center, text(fill: fig-aux, size: 12pt, sym.arrow.t.b))
#let v-down = align(center, text(fill: fig-aux, size: 12pt, sym.arrow.b))
#let h-right = align(center + horizon, text(fill: fig-aux, size: 12pt, sym.arrow.r))
#let h-both = align(center + horizon, text(fill: fig-aux, size: 12pt, sym.arrow.l.r))
#let tag-box(body, fill: fig-plain) = block(
  fill: white,
  stroke: box-stroke(fill),
  radius: 3pt,
  inset: (x: 6pt, y: 8pt),
  align(center + horizon, text(size: 9pt, body)),
)


// ════════════════════════════ 封面 (Cover) ═══════════════════════════════
#{
  set align(center)
  set par(first-line-indent: (amount: 0em, all: false), leading: 1em)

  v(0.6cm)
  text(font: 正文字体, size: 四号)[#竞赛年份 年英特尔杯大学生电子设计竞赛嵌入式系统专题邀请赛]
  v(0.2em)
  text(font: 英文字体, size: 四号)[#竞赛年份 Intel Cup Undergraduate Electronic Design Contest]
  v(0.1em)
  text(font: 英文字体, size: 四号)[#"- Embedded System Design Invitational Contest"]

  v(1.0cm)
  text(font: 华文楷体, size: 32pt)[作品设计报告] // 华文楷体 32pt
  v(0.1em)
  text(font: 英文字体, size: 32pt)[Final Report]

  v(0.8cm)
  image("assets/esdc_logo.jpg", width: 38%)

  v(1.4cm)
  // 报告题目：______（标签 楷体_GB2312 二号 22pt）
  grid(
    columns: (auto, 1fr),
    align: (left + bottom, left + bottom),
    column-gutter: 0.3em,
    text(font: 楷体GB, size: 二号)[报告题目：],
    box(width: 100%, stroke: (bottom: 1pt), inset: (bottom: 4pt))[
      #align(center)[#text(font: 楷体GB, size: 三号)[#报告题目]]
    ],
  )

  v(1.5cm)
  // 学生姓名 / 指导教师 / 参赛学校（楷体_GB2312 三号 16pt）
  let 信息行(标签, 值) = grid(
    columns: (auto, 7.6cm),
    align: (left + bottom, center + bottom),
    column-gutter: 0.3em,
    text(font: 楷体GB, size: 三号)[#标签：],
    box(width: 100%, stroke: (bottom: 1pt), inset: (bottom: 3pt))[
      #text(font: 楷体GB, size: 三号)[#值]
    ],
  )
  block(width: 12.5cm)[
    #set align(center)
    #信息行("学生姓名", 学生姓名)
    #v(0.8cm)
    #信息行("指导教师", 指导教师)
    #v(0.8cm)
    #信息行("参赛学校", 参赛学校)
  ]
}


// ═════════════════════════ 参赛作品原创性声明 ════════════════════════════
#pagebreak()
#{
  set align(center)
  set par(first-line-indent: (amount: 0em, all: false), leading: 1em)
  v(0.4cm)
  text(
    font: 标题字体,
    size: 三号,
    weight: "bold",
  )[#竞赛年份 年（第十三届）英特尔杯大学生电子设计竞赛

    嵌入式AI专题邀请赛]
  v(0.6em)
  text(font: 标题字体, size: 二号, weight: "bold")[参赛作品原创性声明]
}
#v(1.0cm)
#block(width: 100%, inset: (left: 2em))[
  #set par(first-line-indent: (amount: 0em, all: false), leading: 1.6em, justify: true)
  #set text(font: 正文字体, size: 四号)
  #h(2em)本人郑重声明：所呈交的参赛作品报告，是本人和队友独立进行研究工作所取得的成果。除文中已经注明引用的内容外，本论文不包含任何其他个人或集体已经发表或撰写过的作品成果，不侵犯任何第三方的知识产权或其他权利。本人完全意识到本声明的法律结果由本人承担。
]
#v(2.5cm)
#block(width: 100%)[
  #set par(first-line-indent: (amount: 0em, all: false), leading: 2em)
  #set text(font: 正文字体, size: 四号)
  #h(1fr) 参赛队员签名：#h(3cm)
  #v(0.8cm)
  #h(1fr) 日　期：　　　年　　月　　日#h(1.2cm)
]


// ════════════════════════════ 中文摘要 ═══════════════════════════════════
#pagebreak()
// 中文题目：三号黑体居中，上下各空一行
#align(center)[
  #v(一行)
  #text(font: 标题字体, size: 三号, weight: "bold")[#报告题目]
  #v(一行)
  // “摘要”二字：四号黑体居中
  #text(font: 标题字体, size: 四号, weight: "bold")[摘　要]
]
#v(一行)   // 空一行
// 摘要正文：五号宋体，首行缩进二字，单倍行距
#block(width: 100%)[
  #set par(first-line-indent: (amount: 0em, all: false), leading: 1em, justify: true)
  #set text(font: 正文字体, size: 五号)
  #h(2em)#中文摘要
]
#v(一行)   // 空一行
#关键词行(..中文关键词)


// ════════════════════════════ 英文摘要 ABSTRACT ══════════════════════════
#pagebreak()
#align(center)[
  #v(一行)
  // 英文题目：三号 Times New Roman 居中加黑，一律大写
  #text(font: 英文字体, size: 三号, weight: "bold")[#upper(英文题目)]
  #v(一行)
  // ABSTRACT：四号 Times New Roman 居中加黑
  #text(font: 英文字体, size: 四号, weight: "bold")[ABSTRACT]
]
#v(一行)
#block(width: 100%)[
  #set par(first-line-indent: (amount: 0em, all: false), leading: 1em, justify: true)
  #set text(font: 英文字体, size: 五号)
  #h(2em)#英文摘要
]
#v(一行)
#key-words-line(..英文关键词)


// ════════════════════════════ 目  录 ═════════════════════════════════════
#pagebreak()
#align(center)[
  #v(一行)
  #text(font: 标题字体, size: 三号, weight: "bold")[目　录]
  #v(一行)
]
#{
  set text(font: 正文字体, size: 五号)
  set par(leading: 1em, first-line-indent: (amount: 0em, all: false))
  show outline.entry: it => {
    set text(font: 正文字体, size: 五号)
    it
  }
  outline(title: none, depth: 3, indent: 1.5em)
}


// ════════════════════════════ 正文 (Body) ════════════════════════════════
// 正文从第 1 页起编号，启用页脚
#pagebreak()
#set page(footer: 页脚)
#counter(page).update(1)


= 绪论

== 教学背景与核心痛点

高校电子类基础实验是学生由理论走向工程实践的关键环节。学生需依据电路原理图，在面包板上插接电阻、电容、二极管、发光二极管、晶体管和运算放大器等元件，并借助电源、示波器和函数信号发生器等工具来对电路进行实验。这一过程要求学生完成从理论知识到实物操作的完整过程，即由电路原理到元件功能、由二维原理图到面包板孔位、由实验现象到故障原因，任何操作过程的失败都可能使实验停滞。

电子实验课普遍师生比例不匹配，教师难以同时照顾到所有学生。学生向教师提出问题后，教师还需逐项排查元件是否插对、引脚是否接反、孔位是否正确、电源是否误接等基础问题。此类排查高度依赖经验、重复性强，却不能省略。一旦出现极性反接与电源短路可能损坏芯片，存在损坏仪器的风险。

上述场景对智能诊断提出了四个超出常规视觉识别的核心难点。其一，真实图像遮挡严重，导线交叠、元件遮挡引脚与拍摄角度差异都会干扰识别，而常规目标检测只给元件级边界框、无法判定引脚插入哪一孔位，因而诊断必须深入引脚级与孔位级。其二，面包板导通关系不直观，主区按列导通、中缝隔离左右半区、电源轨可能分段，须将物理孔位映射为导通节点，才能判定相邻孔位并非同网、或两引脚短接于同一网络。其三，教学需要可解释、可在界面高亮的证据链而非黑盒结论（具体错误码与证据字段见第四章）。其四，系统须适应边缘环境，实验室网络未必稳定、数据不宜全部上云，故以边缘设备为主要运行平台、降低依赖。

== 现有技术路线及其局限

围绕“判断学生电路是否正确”这一目标，现有技术路线大致可分为三类，各自存在难以回避的局限。

第一类是通用电路仿真软件。以 SPICE 为代表，它面向理想原理图、验证设计层面的正确性，却无法感知面包板上的真实接线，难以发现“原理图正确但实物接错”这一最常见的问题#cite(<spice>)。

第二类是纯规则或模板比较。它借助图同构与引脚角色规则给出确定、可解释的结论#cite(<subgemini>)，但在遇到多余元件、角色标注偏弱、输入输出网络重映射等边界情形时需不断打补丁，易判定过宽或诊断粒度不足。

第三类是端到端大模型直接看图判错。近年多模态大模型展现出强大的视觉理解能力#cite(<llava>)，亦有研究进一步将其用于电路网表故障定位与端到端电路分析辅导#cite(<llm4eda>)#cite(<spiced>)#cite(<e2ecircuit>)；但这类方案多由模型自身承担对错判定、且普遍依赖云端算力，其输出难以审计、易生幻觉，不宜作为正误判定的唯一依据，难以满足教学对安全与可解释的严苛要求。

因此，本文采取折中且工程可落地的路线，由确定性算法构建可验证的结构化事实链承担事实判断，再由智能体在受约束的证据范围内生成解释，从而在可解释性与安全性之间取得平衡。这一“神经—符号”的设计取向贯穿全文，也是本系统区别于上述三类方案的根本所在。

== 项目定位、目的与必要性

LabGuardian 是面向电子实验教学的边缘智能助教系统。与在虚拟环境验证原理的通用仿真不同，它以学生实际搭建的面包板照片为输入，将元件、引脚、孔位与电气连接重建为可验证、可审计的结构化事实，再与参考电路逻辑比较，输出错误位置、成因、风险等级与修改建议，把高度依赖经验的实验巡检形式化为可复现、可解释的诊断流程。

系统主线可形式化为“元件 → 引脚 → 物理孔位 → 导通节点 → 电气网络 → 结构化网表”的逐级事实链，把“某引脚在图像中接近某处”的模糊观察，逐层上升为“某引脚归属某一电气网络”的确定结论。该链路的可靠性，决定了系统能否将像素层面的连接观测转化为确定性的网络归属判断。

== 需求分析与本文工作

面向上述教学场景，系统需同时服务三类用户。学生希望快速知道电路哪里错、为什么错、如何改；教师与助教希望掌握多个实验台状态、定位共性错误以减少重复巡检；系统维护者则关注各模块数据约定稳定、便于后续扩展。

在功能上，系统以“图像接入 → 组件与引脚检测 → 孔位映射 → 拓扑重构 → 参考比较 → 诊断解释”为主线，识别教学常见元件、将引脚吸附至物理孔位并映射为电气节点、合并导线网络输出结构化网表、与逻辑参考电路比较生成差异报告，最终转化为学生可理解的自然语言建议。同时提供人工修正与结果可视化，并在服务端记录运行元数据与硬件遥测。

在非功能上，系统强调准确性、可解释性、低延迟、弱网可用、隐私保护与可扩展性。每个错误都应有证据引用与可视化目标，交互需及时，推理尽量本地运行，新增板型、元件、参考电路与故障案例时无需重写核心链路。

围绕上述需求，本项目的主要工作如下：（1）提出面向真实拍摄照片的引脚级电气网表重构方法，以关键点检测与孔位吸附替代元件级目标检测，将识别粒度下沉至引脚与孔位；（2）以确定性图比对承担对错判断、智能体仅在固定证据范围内生成解释，并由证据一致性校验拦截无依据陈述，构成“神经—符号”的可审计诊断链；（3）面向边缘部署，采用基于固定证据的双教师响应蒸馏与 INT4 量化得到端侧教学解释模型，并在 Intel DK-2500 上以 NPU、iGPU、CPU 三个计算单元分工实现本地推理；（4）通过板端实测与小规模质量检查，验证教学解释链路可在课堂场景中本地运行。

= 系统总体设计

电子实验里，学生在面包板上的接线错误往往从外观看不出来，逐项排查又慢。最简单的做法是把照片和网表丢给大模型、直接问电路对不对，但大模型常会一本正经地给出错误判断，这种幻觉在正确性敏感的实验教学里不可接受。LabGuardian 因此不让大模型参与对错判定，而是把一次诊断拆成三段。视觉感知把照片重构成引脚级网表；确定性图比对（VF2）拿网表和参考电路逐一比，给出可核查的结论和错误码；大模型只把这份已经定好的结论改写成学生听得懂的讲解。把对错交给确定性算法、而不是再训练一个端到端模型，换来的是可审计、不依赖训练数据、每个结论都能回溯到具体引脚和网络；大模型也越不过算法给出的事实边界，这条神经—符号的事实链是整套系统可信的根。

一次完整诊断的运行流程如#ref(<fig:three-chains>)所示。交互端上传面包板俯视照片并选定参考电路后，服务端编排器依次执行各环节，先用关键点检测与孔位吸附重构出引脚级结构化网表，再以 VF2 确定性图比对把网表与参考电路 DSL 比较、产出带证据引用的结构化错误码，最后由端侧教学解释模型在检索约束与证据一致性校验下据错误码生成有依据的教学讲解，并返回交互端可视化。若视觉映射不准确，学生可在前端人工修正孔位、端口或网络角色后调用重算接口，服务端不重跑视觉检测，仅从修正后的元件重新执行拓扑重构、参考验证与解释，以人机协同避免视觉阶段偶发错误导致系统整体不可用。

这条事实链落到工程上有几条不能破的约束。视觉模型只产生候选问题，最终结论必须经板型规则、拓扑分析与验证模块确认；各环节之间只认统一的结构化格式（网表、诊断报告、上下文包），谁都不能私自猜测；视觉难免出错，允许学生把个别引脚或端口改对后重算，不必从头再来；每次运行都留下模型路径、推理参数、版本号与各阶段耗时，连同硬件遥测存档，便于复现与追溯。

系统运行于英特尔 DK-2500 边缘平台（Intel Core Ultra 5 225U），视觉与解释模型经 OpenVINO 适配端侧推理。三类负载的算力需求差异明显，视觉关键点检测是规则的稠密张量运算，常驻 NPU；自回归的解释生成交给 iGPU；图同构、检索、编排与遥测等不规则控制流留在 CPU。三者各管一类任务、互不争抢，使视觉、诊断与控制在 8 GB 内存预算内同时本地运行；各单元的延迟、吞吐与功耗实测见第三章。服务端以 FastAPI 配合 Redis/Celery 组织异步接口，模型以只读方式挂载，并记录模型版本与推理尺寸以保证可复现。

#figure(
  image("assets/arch_overview.png", width: 100%),
  caption: [LabGuardian 神经—符号诊断的总体架构与端到端运行流程。橙框内是视觉感知与引脚级网表重构两步；其下 VF2 确定性图比对据参考电路 DSL 判定连接、产出可审计的结构化错误码；底部端侧教学解释模型在知识库检索与证据一致性校验约束下据错误码生成教学讲解。黑色实线为前向流程，左侧黑色回环表示学生人工修正孔位后触发的重算（不重跑视觉检测）],
) <fig:three-chains>

= 视觉感知与网表重构

本系统将“看图诊断电路”分解为组件检测、引脚检测、孔位映射、拓扑重构和参考比较几个明确的步骤。这几个步骤分别负责一段流程，而智能体仅负责解释，使每一步可独立测试、可视化与修正，降低端到端模型难以审计、易于幻觉的风险。

== 自建引脚级面包板数据集

视觉链路的可靠性首先取决于训练数据，而本场景需要的既非原理图符号数据、亦非印制电路板（PCB）器件数据，而是真实面包板照片上精确到引脚与孔位的细粒度标注。经调研，已有电路类数据集多停留在原理图识别、PCB 缺陷检测或干净网表层面#cite(<amsnet>)，鲜有在“教学面包板 + 引脚级关键点 + 孔位映射 + 真实干扰”四个维度同时满足本任务者。为此本项目自行采集并标注了一套专用数据集，构成本系统视觉感知的基础，也是既有公开资源所缺少的。

数据集采集自真实实验面包板照片，覆盖一阶 RC、共射放大、差分对、UA741 反相/积分/加法六类教学拓扑，并刻意纳入多角度、不同光照与导线遮挡等真实变体，样本本身即贴近课堂实拍的情景、无需合成增强。标注采用“组件级边界框 + 引脚级关键点”双层结构（关键点张量 3×3，每实例至多 3 引脚，记录横纵坐标与可见性），把识别精度从元件级下沉到引脚级。这正是常规检测数据集所不具备、却为电气诊断所必需的粒度。数据集标注电阻、陶瓷电容、电解电容、二极管、发光二极管、跳线、三脚晶体管共七类教学元件，并按训练 / 验证 / 测试留出划分以支持独立评测。

视觉模型经由易到难的渐进路线训练得到，先在单元件照片上验证基础元件的可识别性；再将标注升级为 pose 形式，把任务由“识别元件是什么”推进到“识别引脚在哪里”；继而扩展电位器与双列直插芯片等复杂器件（多脚器件结合封装规则生成引脚候选）；最终过渡到真实实验板上多元件共存与遮挡的综合场景，使数据标注与模型能力同步演进。

最终的 pose 训练运行采用 Ultralytics YOLOv8s-pose#cite(<yolo>)，输入尺寸 960、batch size 为 8、训练 100 轮，启用默认优化器与常规颜色/平移/缩放增强，末 10 轮关闭 mosaic。训练日志显示，模型在第 100 轮的验证集上，组件检测框（B）指标为 precision=0.991、recall=0.989、mAP50=0.991、mAP50-95=0.786，引脚关键点（P）指标为 precision=0.955、recall=0.954、mAP50=0.947、mAP50-95=0.829。上述验证集指标说明模型能较稳定地同时完成组件定位与引脚关键点回归，为孔位映射与拓扑重构提供可用的视觉前提；测试集未参与任何训练与模型选择，留作端到端系统级评测的独立样本。

== 组件检测

组件检测以面包板俯视图为输入，建立全局唯一的元件主实例与编号，作为引脚检测、孔位映射与比对的共同锚点，使下游各阶段对“同一元件”不再产生分歧。输出采用统一结构化格式（编号、类别、封装、置信度与边界框），过滤面包板本体等背景类别。对集成芯片经封装识别推断双列直插 8/14 脚，为后续引脚生成提供依据。

== 全图引脚检测

电气诊断要求识别粒度下沉到引脚级，而常规目标检测无法回答“某引脚究竟插在哪个孔”。直觉方案是先裁剪单个元件框、再在框内回归引脚，但实践发现裁剪会把引脚切到框外并丢失周边上下文，导致系统性漏检。因此系统改为整图关键点检测，在俯视图上以 YOLO-Pose 一次性回归全部引脚关键点，再依类别与边界框的几何约束把引脚归属到对应元件，既避免裁剪误差，又保留完整引脚证据。

模型不可用时，该阶段输出格式兼容的占位结果，保证下游不因模型缺失而结构崩溃。每个引脚记录关键点坐标、可见性与综合置信度，为孔位映射提供完整证据。

在真实面包板上，整图关键点检测的输出经组件归属与孔位映射汇聚为引脚级结构化事实，一例电路实验情景的实际识别效果如#ref(<fig:e2e>)所示。

#figure(
  image("pictures/cadx/e2e_triptych.pdf", width: 85%),
  caption: [视觉事实链实际演示示例（真实模型输出，板上实拍）：(a) 俯视照片输入；(b) 组件检测与类别框；(c) 引脚级关键点汇聚为结构化网表（元件—引脚关联图，IC 引脚按 DIP 封装几何派生）——“像素 → 神经感知 → 符号化结构事实”端到端贯通],
) <fig:e2e>

== 框—点关联与正确的引脚归属

组件检测与引脚检测分属两个模型，前者在整图上给出元件本体的类别与边界框，后者在整图上给出引脚关键点实例。要重构引脚级网表，必须先确定每个引脚实例归属于哪一个元件本体，且不被相邻元件错误认领，否则下游的孔位映射与网表比对都会偏离真实电路。本系统不依赖单一信号，而是对每个引脚实例与每个候选元件框计算一个多信号匹配分数，再以贪心方式做一对一指派。

匹配分数综合以下证据，引脚实例外接框与元件框的交并比、两者中心的邻近度、关键点落入元件框内的比例、引脚跨度与元件尺度的一致性以及检测置信度，并要求引脚类型与元件类别相容（如运算放大器引脚只归属运放本体）。系统按分数从高到低贪心指派，已被占用的引脚实例不再参与后续匹配，从而避免同一引脚被多个元件重复认领。集成电路引脚不依赖关键点检测，而是在识别封装后按双列直插几何规则推导，以应对密集引脚下关键点易混淆的问题。

当某引脚实例对所有候选元件的最高分仍低于阈值时，系统不强行归属，而是将其标记为低置信、在前端暴露候选孔位交由学生确认。这一“多信号打分、贪心一对一指派、低置信拒绝兜底”的关联策略，使引脚到元件的归属在遮挡与密集排布下保持稳定，是后续确定性网表重构可靠的前提。

== 孔位映射与导通节点解析

把“引脚在图像中接近某处”的模糊观测，上升为“引脚归属某一导通节点”的确定结论，是整条事实链中最易产生歧义的一步，同一关键点可能落在相邻孔位之间，单凭最近邻吸附极易误判。孔位映射因此并不简单选取最近孔，而是先用俯视图标定面包板网格（校准失败则回退合成网格并显式标记），再为每个引脚整合关键点坐标、可见性、来源与投影构造观测记录以生成候选孔位，最后依据板型规则把孔位解析为对应的导通节点。

这一步的歧义并非工程实现不足，而是密集小目标检测的固有难点。面包板上的引脚是典型的密集小目标，数十至上百个孔位以毫米级间距规则排布，单个引脚在俯视图中仅占十余像素，相邻孔位外观近乎一致，且常被导线与元件本体部分遮挡。密集小目标的关键点定位是计算机视觉中的难点，即便换用更强的检测与关键点模型，在“引脚究竟落在相邻哪一孔”上也难以做到 100% 正确，孔位级的残余误差不可完全消除。因此系统并不以追求一个不可达的完美视觉为目标，而是正视这一残差、将其显式暴露并交由低成本的人在回路消解。

孔位映射保留而非隐藏不确定性，每个映射后的引脚带有候选孔位、候选节点、是否歧义及原因、综合置信度、吸附距离等信息，使下游能区分高置信映射与需人工复核的低置信映射，与其在低置信处强行给出可能错误的结论，不如显式标注歧义、交由学生一键修正（见#ref(<fig:ambiguity>)）。

#figure(
  image("pictures/cadx/ambiguity.pdf", width: 100%),
  caption: [低置信引脚的歧义可视化：不强行吸附，以虚线环标出候选孔位、交由学生在前端界面修正，把“网匹配歧义”显式化为人机协同介入点],
) <fig:ambiguity>

板型规则承担视觉与电气逻辑的桥梁，依孔位行列归属把物理孔位规范化为稳定导通节点，并支持据节点反查整条导通带的全部孔位、供交互端整带高亮。

在通用孔位识别之外，系统还按器件类型施加几何约束（两脚器件的引脚配对、电位器三孔共线、轴向器件不跨中缝），并由元件外形推断三极管的发射极—基极—集电极极性。这些器件级先验把“像素邻近”修正为“符合物理形态的孔位与极性”，为后续电气比对提供更可靠的引脚级事实。



== 三个计算单元的性能与能效实测

为量化 NPU、iGPU 与 CPU 的分工，项目以 turbostat 按 0.25 秒间隔采样 RAPL 能量计，并在板端以输入分辨率 960 单进程串行采集 60 至 1153 次推理统计，测得 YOLOv8s-pose 关键点检测在 CPU、iGPU、NPU 三种单元上的延迟、吞吐与功耗。其功耗时序如#ref(<fig:power-ts>)所示，NPU 推理期间 CPU 核心与 iGPU 功率曲线全程贴近空闲基线（约 4.4 W），说明 NPU 几乎不占用其他单元资源，为“NPU 负责视觉、iGPU 负责诊断、CPU 负责控制”的三路分工提供了硬件层面的可行性。

#figure(
  image("pictures/cadx/power_timeseries.pdf", width: 88%),
  caption: [YOLOv8s-pose INT8 在 DK-2500 上的 RAPL 功耗时序：三段分别对应 CPU/iGPU/NPU 各持续 15 秒的工作态；NPU 工作时 CPU 与 iGPU 全程贴近空闲基线，是三单元分工、互不争用的硬件前提],
) <fig:power-ts>

各配置详细指标如#ref(<tab:hetero>)所示，NPU INT8 在延迟、吞吐与 P99 三项上均居各配置之首（13.37 ms、74.7 img/s、P99 仅 15.61 ms），满足课堂实时视频流需求；INT8 经 144 张校准图训练后量化得到，模型由 22 MB 压至 11 MB，NPU 吞吐由 FP16 的 60.4 升至 INT8 的 74.7 img/s。

#figure(
  三线表(
    columns: (1fr, 0.9fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align-cells: (center, center, center, center, center, center, center),
    header: ([设备], [精度], [负载(s)], [均值(ms)], [P95(ms)], [P99(ms)], [img/s]),
    rows: (
      ([CPU], [FP16], [0.14], [92.44], [96.74], [98.92], [10.8]),
      ([CPU], [INT8], [0.24], [29.02], [30.13], [30.65], [34.5]),
      ([iGPU], [FP16], [0.43], [26.87], [27.32], [28.18], [37.2]),
      ([iGPU], [INT8], [2.85], [18.26], [19.29], [20.11], [54.7]),
      ([NPU], [FP16], [1.01], [16.55], [16.64], [17.67], [60.4]),
      ([NPU], [INT8], [1.20], [13.37], [13.75], [15.61], [74.7]),
    ),
  ),
  caption: [YOLOv8s-pose 在 DK-2500 上六种设备—精度配置的延迟与吞吐实测（输入分辨率 960）],
) <tab:hetero>

能效上，NPU INT8 增量功耗仅 4.12 W、单次推理能耗 114.2 mJ、性能功耗比 18.1 ips/W，较 CPU INT8 节能约 7.1 倍。实测印证这种分工，视觉常驻负载交给 NPU，既释放 CPU 与 iGPU，又在功耗预算内满足实时性。系统另提供 5 Hz 硬件遥测与降级能力。

= 电气重构与确定性诊断

本章是“神经—符号”中的符号侧，它不依赖任何神经网络，对错判断由图论算法以确定、可复现、可审计的方式给出，因而不会在安全敏感的对错问题上产生幻觉。

== 拓扑重构与结构化网表

视觉阶段给出“哪个引脚落在哪个孔”，电气诊断需要“哪些引脚同属一个导通网络”，拓扑重构完成这一跨越。读取孔位映射后的元件与引脚来构造电路实际连接关系，以图结构表示元件—网络关系，用并查集把导线连接的等电位孔位合并为统一网络。这里有一个易被忽视的陷阱，若沿用上游旧的节点编号，一旦人工修正了某个孔位，旧编号残留便会致错。因此系统坚持以物理孔位为唯一可信来源、据孔位重新解析导通节点。在最终的元件—网络二分图中，导线不作为元件参与拓扑，仅用于合并网络。若某非导线元件的多个引脚落入同一网络，则标记为同网络以供短路风险判断。

该部分流程的核心产物是结构化网表。一个保留元件、引脚、网络、节点索引与板型拓扑的结构化对象，被交互端、验证模块与智能体共同消费，亦可导出拓扑级 SPICE 网表。它同时服务于电气比较与可视化定位，选中某网络即可高亮其全部相关孔位（结构化网表及其拓扑级 SPICE 导出的实例见#ref(<fig:netlist>)）。

#figure(
  image("pictures/cadx/netlist_info.pdf", width: 100%),
  caption: [结构化网表可视化（board_1，真实管线输出；电源与地依实际接线人工校正）：(a) 面包板视图——同色引脚同属一个电气节点，电源/地网络加深描边；(b) 拓扑级电路图——网络为节点、元件为边，导线隐式合并入网络（IC 双电源 VCC/VEE 与地 GND 清晰可辨）；(c) 由该网表导出的拓扑级 SPICE 片段（GND 映射为节点 0，元件取值留作占位）],
) <fig:netlist>

== 参考电路的领域特定语言

参考电路的正确性直接决定诊断可信度。系统不手写网表 JSON，而以一套嵌入式 Python 领域特定语言（DSL）声明逻辑参考电路，把“作者意图”与“机器可比对结构”分离，Circuit 承载网络、元件、对称组与等价选项，Net 携带语义角色（signal / input / output / power / ground）与角色标签，Pin 可显式标注不连接（no-connect），并以等价规则（忽略孔位与元件编号、忽略无极性引脚顺序、允许多余导线）表达比对意图，最终编译为统一逻辑参考 JSON。新增参考电路只需书写数十行接近原理图的 DSL，既降低出错概率，又与比对器保持稳定数据约定。

== 确定性图比对算法

此处面临一对看似矛盾的要求，学生在面包板上的摆放千差万别，不能因孔位不同就判错；但只要电气逻辑接错，又必须准确指出。逐孔位的硬规则只能满足其一，无法实现两全。本系统的解决方案是把比对提升到逻辑层，在元件—网络二分图上、只对照逻辑参考电路，使“摆放不同但逻辑等价”判为正确、“逻辑网络接错”判为错误。算法分级进行，首先尝试完整图同构匹配（采用 VF2 子图同构算法#cite(<vf2>)，基于 networkx 图论库#cite(<networkx>)实现），节点按元件类型与网络角色匹配、边按引脚角色匹配。在同构之前，系统先做一次模糊组件对齐与规范名（canonical-name）角色传播，把参考电路的语义（如 INV、VOUT）传播到学生电路的匿名网络上，使下游消费者看到富语义；此步只更新网表语义而不重建结构图，以免干扰结构匹配的判定。

当完整同构失败时，算法逐级降级。先判断学生电路是否为参考电路的子图或包含关系，仍不成立时，才以图编辑距离或近似相似度给出错接报告。匹配规则采用“严格/宽松”分级，电源与地、以及功能引脚严格匹配；电阻、电容、导线等无极性两脚器件忽略引脚顺序；并允许合理的额外导线。相比逐孔位规则，该分级显著降低了因摆放差异导致的误报；相比纯文本规则，又对关键电气语义保持刚性约束。这正是把对错判断交给符号系统、而非交给易幻觉大模型的根本理由。

算法核心不是单次布尔判断，而是一条可解释的级联判定链。先尽量证明电路正确，再逐级识别失败类型并转写为稳定错误码，每个结论都能回溯到具体匹配阶段（一例完整比对与错误码输出见#ref(<fig:compare-cascade>)），交互端据此高亮，智能体只能引用这些结构化事实而不能臆测故障。

#figure(
  image("assets/vf2_compare.png", width: 85%),
  caption: [确定性图比对的一个完整实例，也是总体架构图中符号诊断环节的细化展开。上行为参考电路 DSL，下行为缺反馈电阻 $R_f$ 的实际接线，完整图同构在 INV–VOUT 处失败，逐级降级后定位到缺失元件，并统一转写为稳定错误码 COMPONENT\_MISSING 与 INCOMPLETE\_CIRCUIT（见#ref(<tab:errcode>)）。整个判定确定、可回溯到具体引脚与网络，不依赖学习模型],
) <fig:compare-cascade>

== 拓扑模板与三层语义匹配

纯图比对需要一份确定的参考电路，但同一教学拓扑常有多种正确的实现方式，以单一参考硬比较极易误报。为此系统引入拓扑模板，把每类规范拓扑表达为“偏规范”，以三层语义刻画结构。required（必需，如共射的三极管、集电极电阻、输入/输出耦合电容）缺失则不匹配；optional（可选，如发射极旁路电容 C#sub[E]、偏置补偿电阻 R#sub[p]）可缺不扣分；forbidden（禁止，如反相放大器中出现的反馈电容，实为积分器）出现即降级或否决。另以变体与重数容纳多种合法实现，并声明参数化不变量。

匹配以子图同构搜索模板在学生电路图中的嵌入，按必需边占比计分、forbidden 命中扣分。模板层与图比对并行、对管线只读，把绪论所述“纯规则需不断打补丁”的边界情形系统化容纳进来。

== 诊断报告与错误码

参考比较与模板匹配的结论汇聚为结构化诊断报告，每条诊断项含错误码、错误族、严重程度、建议动作、证据引用及涉及的元件、引脚与孔位等字段。错误码采用稳定的确定性词表（如#ref(<tab:errcode>)所示），它也是后文检索约束中“验证器↔知识库”桥接的关键，故障案例正是依据错误码被精确召回。

#figure(
  三线表(
    columns: (2.0fr, 0.8fr, 2.3fr),
    align-cells: (left, center, left),
    header: ([错误码], [错误族], [含义与典型成因]),
    rows: (
      ([COMPONENT_MISSING], [缺件], [参考电路所需元件在当前电路中缺失]),
      ([WRONG_CONNECTION], [接线], [引脚连接到了与参考不一致的电气网络]),
      ([SHORT_CIRCUIT], [短路], [本应分离的关键网络（电源/地、输入/输出）被合并]),
      ([OPEN_CIRCUIT], [开路], [本应共网的引脚被分到不同网络，连接断开]),
      ([OUTPUT_NODE_MISMATCH], [节点], [输出节点角色与参考不符（输入/电源/地同理）]),
      ([CRITICAL_EXTRA_CONNECTION], [多接], [关键网络上存在参考未要求的额外接线]),
      ([INCOMPLETE_CIRCUIT], [未完成], [当前电路仅匹配参考电路的一部分]),
    ),
  ),
  caption: [诊断报告常见错误码（确定性图比对输出的稳定词表，节选）],
) <tab:errcode>

诊断报告还包含面向交互端的高亮协议，把每条诊断项的证据引用转换为可直接绘制的高亮目标，智能体生成解释时复用同一份协议，使自然语言说明与界面定位指向同一份事实。


= 智能解释与人机协同

得到结构化网表与诊断报告后，系统进行事实链最后一环，智能体在受控事实约束下生成解释，知识检索安全补充背景，交互端呈现证据并定位错误，人工修正与重算形成闭环。

== 诊断智能体与按需证据注入

最直接的做法是把完整网表与知识库塞进大模型上下文任其推理，但边缘小模型上下文与内存紧张，且一旦看到全部原始事实，便有“重新判断对错”的空间而产生无依据扩展。系统因此采用按需证据注入（Push-based Context Management, PCM），按错误类型、风险等级、场景与用户问题，从课堂状态编译出仅含当前必需事实、允许工具与证据引用的最小上下文包并估算 token 规模。智能体只能看到被注入的内容，不会越过验证模块猜测孔位或网络，这种主动压缩对内存受限的边缘部署尤为关键。

诊断智能体统一编排诊断、概念讲解、操作指导与混合问答四类教学意图，共用同一张状态图，仅按意图切换工具白名单、校验规则与回答模板；工具选择进一步取决于错误族（如短路类调用网表追踪与板型查询），智能体据此动态选工具#cite(<react>)，而非把所有知识与历史塞入上下文。意图判定以确定性关键词分类为主，端侧小模型不再承担意图判断，只负责根据既定意图与固定证据生成回答。

状态图以 LangGraph 为编排外壳，管理节点（错误分类、上下文构建、规划、观察、反思、回答验证、修复、定稿）的流转，并为最小化边缘部署提供行为等价的确定性顺序回退路径。其核心是职责分离，视觉、拓扑、比较与验证模块用于确定电路事实，大模型仅用于将问题改写为自然语言而不介入判定；反思环节设有证据一致性校验，由一组固定规则给回答把关，回答必须引用证据、命中相应错误码、危险场景先提醒断电，任一条不满足都判为不合格并触发修复，小模型无法跳过这一步。即便解释模型仅十亿级参数，一旦偏离既定事实即被结构化拦截，无需依赖提示工程。这正是端侧小模型在正确性敏感场景可靠应用的前提。

== 知识检索约束与安全降级

为避免“训练一套知识、部署另一套”的不一致，系统对智能体的检索增强生成（RAG）#cite(<rag>)施加可审计约束，合法知识源仅有教学场景库、故障案例库、器件手册库与电路知识库四个通道，另加工位状态、流水线快照与参考电路等结构化事实通道（如#ref(<tab:retrieval-contract>)所示）。早期基于通用向量库的文档检索仅保留给后台调试，禁止进入主链路或蒸馏管线，以避免分布漂移、云端依赖与内容污染。

#figure(
  三线表(
    columns: (1.25fr, 2.05fr, 2.55fr),
    align-cells: (left, left, left),
    header: ([通道], [内容], [约束作用]),
    rows: (
      ([教学场景库], [六类 demo 场景的目标、步骤、测量点与安全提示], [回答先对应当前拓扑，避免跨实验串场]),
      ([故障案例库], [按场景、错误标签、错误码组织的典型故障与修复步骤], [只有命中当前错误码才返回，防止凭空举例]),
      (
        [器件手册库],
        [UA741、LM324、NE555、BJT 等结构化 datasheet 与本地嵌入],
        [场景白名单过滤无关芯片，端侧无外网依赖],
      ),
      ([电路知识库], [放大器、积分器、比较器等原理知识], [只补充教学解释，不改写诊断事实]),
      (
        [结构化事实],
        [工位状态、pipeline 快照、reference circuit、error codes],
        [作为最高优先级证据，所有解释必须引用它],
      ),
    ),
  ),
  caption: [Agent/RAG 检索约束的合法通道与约束作用],
) <tab:retrieval-contract>

上述约定让蒸馏训练与板端部署保持一致，蒸馏数据生成与板端部署使用同一套代码、知识与场景白名单，并由启动前自检脚本校验两端等价。它把“可用知识的边界”做成可审计的工程约束，场景白名单按拓扑过滤器件手册，使反相放大器的问题不会召回无关的定时器芯片；故障案例仅在错误码命中时返回，召回键正是第四章图比对输出的错误码词表。检索缺失时系统 fail-closed，蒸馏样本拒绝生成、部署端回退确定性模板，宁可少答也不让错误默认值污染结论。这一取向与近年电子设计自动化语言模型“以确定性结构约束生成”的方向一致#cite(<llm4eda>)。

== 交互端设计与结果呈现

交互界面以 React、Vite 与 TypeScript 构建，职责是把服务端的结构化事实清晰呈现给师生。主区提供两种视图，网表视图支持孔位、端口、网络角色与引脚极性的人工修正，图像视图在原图上渲染识别框与高亮目标。点选某条诊断即据其证据引用定位到元件、引脚与孔位，使自然语言解释与界面定位指向同一份事实。

== 人工修正闭环

人工修正时，系统结合用户对端口、网络角色、引脚极性等的修改生成补丁，调用重算接口重新执行拓扑重构与比较，不重跑视觉检测，以极小代价纠正视觉阶段偶发偏差。视觉模型难免漏检、误检或吸附偏差，LabGuardian 保留视觉阶段的大部分事实、只对有争议的引脚或端口做局部修改再重新判断，把 AI 定位为助教而非裁判。显式保留不确定性、低成本纠正回路，正是面对必然带有干扰的真实照片输入时仍能可靠服务教学的工程基础。

作为本章诊断闭环的整体印证，#ref(<fig:diag-demo>)给出一例反相放大器双故障的端到端诊断，系统在真实故障板上同时定位“输入电阻错接至偏置脚”与“运放负电源缺失”两处接线错误，由确定性比对输出稳定错误码、再由端侧学生模型生成有依据的讲解，使自然语言解释与界面高亮指向同一份结构化事实。这正是从真实照片输入到确定性诊断、再到受约束解释这一闭环在真实故障样本上的完整呈现。

#figure(
  image("pictures/cadx/diag_demo.pdf", width: 100%),
  caption: [反相放大器双故障端到端诊断示例（板上实拍 + 真实管线输出）：(a) 故障板的组件/引脚检测与错误定位——①输入电阻错接至偏置/调零脚 pin1（应接反相输入 pin2），②运放 pin4（V−）未接负电源 VEE；(b) 确定性比对输出的结构化错误码（WRONG_CONNECTION、OPEN_CIRCUIT）与端侧学生模型生成的有依据的讲解，自然语言解释与错误定位指向同一份事实],
) <fig:diag-demo>



== 基于固定诊断证据的端侧教学解释模型训练与部署

为使教学解释环节能够在边缘端本地运行，本文采用基于固定诊断证据的双教师响应蒸馏方法训练端侧小语言模型。需要强调的是，语言模型不参与电路正误判定；电路连接关系、错误类型和证据引用均由前述确定性图比对模块给出，端侧模型只学习如何在给定证据范围内组织语言、面向学生生成教学解释。

具体流程如下。首先，系统围绕典型教学电路、常见接线错误和学生常问问题构造候选问题，并运行正式诊断链路，为每个问题固定对应的结构化证据，包括错误码、涉及元件、引脚位置、网络关系、检索知识和风险等级。然后，使用 Qwen3-32B 与 DeepSeek-V3 作为双教师模型，在同一份固定证据约束下分别生成候选解释。教师回答并不直接进入训练集，而是经过证据引用校验、长度过滤、安全过滤和一致性筛选，剔除缺乏依据、偏离当前场景或被降级为“证据不足”的回答。最终，将“学生问题 + 固定诊断证据”作为输入，将筛选后的教师解释作为目标输出，构建监督微调数据集，用于训练端侧学生模型。

学生模型以 Qwen2.5-1.5B-Instruct 为基座，采用 LoRA 进行参数高效微调。训练阶段冻结基座模型参数，仅更新 LoRA 适配器；训练完成后将 LoRA 权重与基座模型合并，再进行 INT4 量化并导出为 OpenVINO 部署模型。板端运行时，模型接收确定性诊断模块输出的错误码和检索证据，只生成教学解释，不重新判断电路正误；生成结果还需经过证据一致性校验，若出现无依据扩展则被拦截或退回模板解释。

#figure(
  image("assets/distill_arch.png", width: 100%),
  caption: [基于固定证据的双教师检索增强蒸馏流程：本地 Qwen3-32B 与云端 DeepSeek-V3 在同一份固定结构化证据上作答，候选池经筛样（引用合规、长度达标、未降级为“证据不足”）得到 3450 条 SFT 数据，用以微调 Qwen2.5-1.5B 学生模型并经 INT4 量化部署；训练数据生成与板端部署共用同一检索约束],
) <fig:train-deploy-loop>

=== 双教师响应蒸馏数据构建

蒸馏数据不是让教师模型自由发挥生成，而是围绕真实课堂问题在固定证据约束下构建。项目首先从典型教学电路、常见接线错误和学生常问问题出发生成候选问题，再运行正式诊断链路，为每个问题固定对应的结构化证据。固定证据至少包含场景标识、错误码、涉事元件、引脚位置、网络关系、检索知识、风险等级、允许工具与回答规则，使教师模型在回答时只能围绕当前诊断事实组织语言，而不能重新猜测电路状态。

在教师侧，项目使用本地部署的 Qwen3-32B#cite(<qwen3>) 与云端 DeepSeek-V3#cite(<deepseekv3>) 作为双教师，在同一份固定证据约束下分别生成候选解释。教师回答并不直接进入训练集，而要先经过证据引用校验、长度过滤、安全过滤和一致性筛选，剔除缺乏依据、偏离当前场景或被降级为“证据不足”的回答。统计结果显示，4990 条候选教师输出中，3466 条满足可训练条件，最终保留 3450 条正式 SFT 样本；在 546 条双教师重叠题上，双教师合池的可用覆盖率为 82.42%，较单独使用 DeepSeek-V3 的 67.77% 提高了 14.65 个百分点。这说明双教师的作用主要不是“追求更华丽的文字”，而是提高固定证据下可保留样本的覆盖率。

#figure(
  三线表(
    columns: (1.2fr, 2.6fr),
    align-cells: (left, left),
    header: ([字段], [样例内容（节选）]),
    rows: (
      (
        [system],
        [你是 LabGuardian 课堂实验助教；回答必须严格依据给定 fixed evidence，不得编造器件、引脚、节点、网表或实验现象],
      ),
      ([instruction], [我信号源和示波器没共地，RC 波形乱跳，是不是地线没接好？]),
      (
        [input],
        [scene_id=exp_first_order_rc；risk_level=danger；error_codes=COMPONENT_SHORTED_SAME_NET；finding: component=SCOPE_GND, pin=gnd_clip；并附带允许工具、证据引用要求与工具检索结果],
      ),
      (
        [output],
        [先给结论，再给依据，再给修改步骤；例如先提醒断电，再说明示波器地夹同网短接风险，最后给出复查接地点与共地关系的操作建议],
      ),
    ),
  ),
  caption: [监督微调样本格式示例。训练样本的输入不是“裸问题”，而是“学生问题 + fixed evidence”；目标输出是经筛选后的教师解释],
) <tab:sft-sample>

=== 学生模型 LoRA 微调

学生模型以 Qwen2.5-1.5B-Instruct#cite(<qwen25>) 为基座，训练目标采用 next-token 监督微调，即把筛选后的教师解释作为目标输出，学习 “问题 + 固定证据 → 教学解释” 这一映射。训练阶段冻结基座参数，仅更新 LoRA 适配器，使蒸馏环节保持参数高效并便于后续权重合并与端侧部署。

LoRA 插入位置覆盖Qwen2.5-1.5B-Instruct的注意力层与前馈层线性投影；按训练方案采用轻量 LoRA 配置（rank=32、alpha=64、dropout=0.05），正式训练配置进一步固定为lora_target=all、cutoff_len=3072、per_device_train_batch_size=2、gradient_accumulation_steps=8、num_train_epochs=3、learning_rate=5e-5、warmup_ratio=0.05、weight_decay=0.01、optim=adamw_torch、bf16=true，并以 5% 验证集、每 200 step 评估一次的方式进行训练。这里保留这些参数，不是为了包装性能，而是为了说明学生模型确实按可复现配置完成了微调。

#figure(
  kind: image,
  block(
    stroke: 0.7pt + black,
    inset: (x: 10pt, y: 8pt),
    radius: 3pt,
  )[
    #set par(first-line-indent: (amount: 0em, all: false), leading: 0.7em, spacing: 0.4em, justify: false)
    #grid(
      columns: (1.15fr, auto, 2fr, auto, 1.1fr),
      column-gutter: 6pt,
      row-gutter: 5pt,
      align: center + horizon,

      [#tag-box([*Qwen2.5-1.5B-Instruct 基座*], fill: fig-emph)],
      [],
      [#tag-box([*Transformer Block 内部结构*], fill: fig-emph)],
      [],
      [#tag-box([*训练 / 部署结果*], fill: fig-emph)],

      [#flow-node([输入嵌入
        Token / Position Embedding
        基座参数冻结])],
      [#h-right],
      [#flow-node([Self-Attention
        主干线性投影：q_proj k_proj v_proj o_proj
        LoRA 以低秩分支并联插入])],
      [#h-right],
      [#flow-node([训练阶段
        仅更新 LoRA Adapter
        基座权重保持冻结])],

      [], [], [#v-down], [], [#v-down],

      [#flow-node([Transformer Block × N
        保持原有 Qwen 主干结构
        不改变推理接口])],
      [#h-right],
      [#flow-node([MLP
        主干线性投影：gate_proj up_proj down_proj
        LoRA 同样插入这些层])],
      [#h-right],
      [#flow-node([部署阶段
        LoRA 与基座权重合并
        再做 INT4 量化与 OpenVINO 导出])],

      [], [], [#v-down], [], [#v-down],

      [#flow-node([LM Head
        输出面向学生的教学解释 token])],
      [#h-right],
      [#tag-box(
        [LoRA 配置
          rank = 32
          alpha = 64
          dropout = 0.05],
        fill: fig-warm,
      )],
      [#h-right],
      [#flow-node([板端运行
        接收固定证据
        只生成教学解释])],
    )
  ],
  caption: [学生模型 LoRA 结构示意。LoRA 不改变 Qwen 基座的总体结构，只在主要线性投影层上附加可训练低秩分支，训练结束后再与基座权重合并],
) <fig:lora-structure>

=== INT4 量化与 OpenVINO 端侧部署

训练完成后，项目先将 LoRA 权重与基座模型合并，再进行 INT4 量化#cite(<awq>)并导出为 OpenVINO 部署模型。部署到 DK-2500 后，板端只接收确定性诊断模块输出的错误码、风险等级与检索证据，不重新判断电路正误；若输出超出证据边界，则由证据一致性校验拦截。也就是说，端侧模型承担的是“把确定性诊断结果讲清楚”的工作，而不是替代诊断算法本身。

板端部署默认使用 iGPU 运行语言模型，NPU 主要承担视觉推理，CPU 负责拓扑分析、检索、调度和校验。这里给出的实测数据只用于证明“板子上确实能跑”，不追求论文式性能包装。根据板端真实日志，INT4 OpenVINO 学生模型包体约 941.5 MB，加载约 3.74 s，首 token 延迟约 63.9 ms，解码吞吐约 23.2 token/s，生成一条约 128 token 的教学解释约需 5.52 s，运行峰值内存约 1.36 GB；在整机空载 4.42 W 条件下，解释生成阶段整封装平均功率约 10.16 W，说明其能够与视觉链路共同运行在 8 GB 内存预算内。

#figure(
  三线表(
    columns: (1.6fr, 1.2fr, 2.2fr),
    align-cells: (left, center, left),
    header: ([部署项], [实测结果], [说明]),
    rows: (
      ([部署模型], [Qwen2.5-1.5B-Instruct + LoRA 合并 + INT4], [OpenVINO 导出后在 DK-2500 板端运行]),
      ([默认计算单元], [iGPU], [CPU 负责检索、图比对与控制；NPU 负责视觉模型]),
      ([模型包体], [约 941.5 MB], [板端可直接加载，无需外网]),
      ([加载时间], [3.74 s], [冷启动可接受]),
      ([首 token 延迟], [63.9 ms], [交互启动等待较短]),
      ([解码吞吐], [23.2 token/s], [约 128 token 回答耗时 5.52 s]),
      ([峰值内存], [1.36 GB], [板载 8 GB 内存下可与其他模块共存]),
      ([推理阶段功耗], [10.16 W], [空载约 4.42 W；用于证明端侧部署可行]),
    ),
  ),
  caption: [INT4 OpenVINO 端侧部署可行性实测。这里保留的是“是否能本地运行”的证据，而非追求横向性能排名],
) <tab:edge-deploy-proof>

=== 输出示例与质量评测

为证明端侧教学解释链路真实可用，本项目保留一条板端真实输入、真实输出与校验结果示例，并给出 30 题初步质量检查。需要说明的是，这里的评测目的不是证明模型超过教师或超过云端模型，而是验证“固定证据 -> 端侧解释 -> 校验放行”这一链路在课堂问题上能够稳定工作。

#figure(
  三线表(
    columns: (1.15fr, 2.65fr),
    align-cells: (left, left),
    header: ([项目], [内容]),
    rows: (
      ([真实输入], [学生问题：我搭的一阶 RC 低通滤波器输出端几乎没有信号，怎么排查？]),
      (
        [固定证据],
        [scene_id=exp_first_order_rc；risk_level=warning；要求先断电，优先检查 C1 是否悬空或接触不良，并检查节点连通与接地参考],
      ),
      (
        [端侧真实输出],
        [先断电，检查 C1 是否悬空，然后检查输出端是否接错节点，再检查输入与地是否共参考。操作顺序：先断电，再检查元件接触、孔位和节点连通],
      ),
      (
        [证据一致性校验],
        [通过。输出命中“先断电 / C1 悬空 / 节点连通”三项关键证据，未新增不存在的器件、引脚或错误码；因此允许直接返回学生端],
      ),
    ),
  ),
  caption: [端侧教学解释真实示例与校验结果。该回答来自板端学生模型真实输出，校验关注的是是否严格落在给定证据范围内],
) <tab:edge-output-example>

30 题初步质量检查结果表明，端侧模型已经具备课堂可用性，但仍保留了清晰的改进方向。当前 30 题中整体通过率为 90.0%，其中概念讲解、实验指导与混合问答三个类别通过率均为 100%，诊断类问题通过率为 76.9%。结合自动评分记录可以看出，当前主要短板不是“答不出来”，而是部分回答教学引导性偏弱，更像操作清单；后续迭代重点应放在诊断类排查顺序和教学启发性，而不是继续包装横向模型分数。

#figure(
  三线表(
    columns: (1.6fr, 1fr, 1fr, 2.1fr),
    align-cells: (left, center, center, left),
    header: ([检查项], [题数], [通过率], [说明]),
    rows: (
      ([整体], [30], [90.0%], [用于验证端侧链路是否可用]),
      ([概念讲解], [8], [100.0%], [定义、公式与原理类问题较稳定]),
      ([实验指导], [5], [100.0%], [步骤性问题回答较完整]),
      ([混合问答], [4], [100.0%], [兼顾原理与操作的场景可覆盖]),
      ([诊断排查], [13], [76.9%], [仍需加强排查顺序与启发式表达]),
    ),
  ),
  caption: [30 题初步质量检查结果。该结果用于说明端侧教学解释链路已经跑通并具备课堂使用基础],
) <tab:quality-check-30>

= 结论与展望


#ref(<tab:key-results>)先汇总关键量化结果，主要证据不集中于单一模型精度，而是覆盖数据资产、确定性算法、检索约束、模型压缩、边缘部署与工程测试六个维度，对应“把真实感知、符号判断、智能解释与边缘部署放在同一套可验证闭环中”的设计取向。

#figure(
  三线表(
    columns: (1.25fr, 2.4fr, 2.1fr),
    align-cells: (left, left, left),
    header: ([维度], [指标], [结果]),
    rows: (
      ([数据资产], [自建引脚级视觉数据集], [自采真实面包板照片，引脚级关键点 + 孔位映射标注]),
      ([视觉部署], [DK-2500 NPU INT8 延迟/吞吐], [13.37 ms，74.7 img/s，P99 15.61 ms]),
      ([视觉能效], [NPU INT8 增量功耗/单次能耗], [约 4.12 W，114.2 mJ，18.1 ips/W]),
      ([解释部署], [INT4 学生模型包体/峰值内存], [约 0.94 GB，峰值约 1.36 GB，可在板端本地运行]),
      ([教学解释], [30 题初步质量检查], [整体通过率 90.0%，其中诊断类通过率 76.9%]),
      ([证据约束], [固定证据 + 一致性校验], [端侧模型只在给定证据范围内生成解释，越界时拦截或回退模板]),
      ([工程质量], [单元与约定测试], [约 900+ 用例，整体通过率约 99%]),
    ),
  ),
  caption: [LabGuardian 关键量化结果汇总],
) <tab:key-results>


本文提出并实现了 LabGuardian，一个面向电子实验教学、运行于英特尔边缘平台的神经—符号电路诊断系统。系统以真实拍摄的面包板照片为起点，经关键点检测与孔位吸附重构引脚级电气网表，由确定性图比对承担可审计的对错判断，再由受约束的智能体在证据一致性校验约束下生成有依据的解释。教学解释模型通过学习双教师在固定证据下生成的回答获得，并经 INT4 量化部署于 DK-2500，以 NPU、iGPU、CPU 三个计算单元分工实现本地推理。板端实测表明，系统可在 8 GB 内存预算内完成视觉识别与端侧解释；30 题初步质量检查也说明其已具备课堂使用基础，而教学解释的事实正确性由固定证据边界与证据一致性校验共同保证。

与既有工作相比，本系统主要有三点不同。第一，面向必然带有干扰的真实照片输入，而非理想的干净网表。第二，以神经—符号的思路把对错判断交给可审计的符号系统、把语言表达交给受约束的小模型。第三，让训练阶段与板端部署使用同一套检索约束和固定证据边界，再配合证据一致性校验，把“防止无依据扩展”做成工程上可审计的约束而非提示技巧。这样一个十亿级小模型也能在对正确性要求较高的教学场景中、于边缘设备上稳定运行。

== 局限

系统在确定性链路、检索约束与边缘部署上的能力已获实测支撑，但仍有不足。当前质量检查题量仅 30 题，诊断类题目仍有提升空间；蒸馏学生在没有模板兜底时的教学启发性受参数规模所限；端到端从真实照片到正确诊断的成功率仍需在更大真板集上统计。



== 展望

后续工作将集中于四个方向，把当前 30 题初步检查扩展为更大规模、多人复核的课堂题集；针对 diagnostic 类题目继续增强蒸馏数据与回答约束，降低排查顺序与关键检查点的漏答率；在更大规模真板集上统计“照片→诊断”的端到端成功率；并持续扩充教学场景、故障案例与器件手册知识库，使系统覆盖更多课程实验。






// ════════════════════════════ 参考文献 ═══════════════════════════════════
// 不编章号，三号黑体居中；条目按出现次序用中括号数字连续编号，顶格、五号宋体、单倍行距
#heading(level: 1, numbering: none)[参考文献]
#{
  set text(font: 正文字体, size: 五号)
  set par(leading: 1em, first-line-indent: (amount: 0em, all: false))
  bibliography("refs.bib", title: none, style: "gb-7714-2015-numeric")
}


#heading(level: 1, numbering: none)[附录]

#block[
  #set par(first-line-indent: (amount: 2em, all: true), leading: 1em)
  *附录 A　源代码与程序清单.* 本作品完整源代码随电子附件一并提交，附件包含后端服务、前端交互界面、视觉诊断流水线、知识库、边缘部署说明、配置示例和测试程序。报告正文仅列出主要代码结构与关键程序功能，完整可运行代码以电子附件中的项目目录为准。

  源码附件建议命名为 #text(font: 英文字体)[LabGuardian_Source_Code.zip]，其中 #text(font: 英文字体)[LabGuardian-Server/] 保存后端服务、诊断流水线、知识库、测试和部署脚本，#text(font: 英文字体)[LabGuardian-web/] 保存前端交互界面源码。附件中保留源码、配置示例、测试样例、说明文档和必要脚本；不包含本地虚拟环境、依赖缓存、运行日志、上传缓存、个人密钥和真实环境变量。较大的模型权重、数据集或量化模型如需单独提交，应在 README 中注明文件名、用途、放置路径和运行方式。
]

#figure(
  三线表(
    columns: (1.15fr, 2.1fr, 3.55fr),
    align-cells: (center, left, left),
    header: ([类别], [目录或文件], [功能说明]),
    rows: (
      ([后端入口], [app/main.py], [启动 FastAPI 应用，挂载各类 API 路由与服务配置。]),
      ([API 接口], [app/api/v1/pipeline.py], [提供流水线运行接口，接收面包板图像与参考电路配置，返回结构化诊断结果。]),
      ([智能体接口], [app/api/v1/angnt.py], [提供教学解释问答接口，接收诊断证据并返回面向学生的说明与建议。]),
      (
        [服务层],
        [app/services/pipeline_service.py],
        [组织视觉识别、孔位映射、网表构建、图比对和语义分析等阶段的调用。],
      ),
      (
        [流水线编排],
        [app/pipeline/orchestrator.py],
        [控制 S1 至 S5 各阶段的执行顺序、状态传递、异常处理和运行元数据记录。],
      ),
      (
        [组件检测],
        [app/pipeline/stages/s1_detect.py],
        [使用俯视图建立元件主实例，生成全局 component_id 与组件类型、封装和边界框信息。],
      ),
      (
        [引脚检测],
        [app/pipeline/stages/s1b_pin_detect.py],
        [调用整图 YOLO-Pose 检测引脚关键点，并将引脚归属到对应组件。],
      ),
      (
        [孔位映射],
        [app/pipeline/stages/s2_mapping.py],
        [将引脚关键点映射到面包板 hole_id 与 electrical_node_id，并保留候选孔位和歧义信息。],
      ),
      (
        [拓扑构建],
        [app/pipeline/stages/s3_topology.py],
        [根据组件、引脚和孔位信息构建拓扑图，导出 netlist_v2 结构化电气网表。],
      ),
      (
        [诊断校验],
        [app/pipeline/stages/s4_validate.py],
        [调用参考电路比较模块，生成错误码、风险等级、建议动作和证据引用。],
      ),
      (
        [语义分析],
        [app/pipeline/stages/s5_semantic_analysis.py],
        [把诊断事实整理为教学解释输入，使语言模型只消费已验证证据。],
      ),
      ([参考电路 DSL], [app/domain/dsl/], [描述和编译参考电路，生成可用于图比对的标准逻辑结构。]),
      (
        [确定性图比对],
        [app/domain/compare/],
        [在元件-网络图上比较学生电路与参考电路，定位缺失、短路、开路和错接等问题。],
      ),
      (
        [知识与智能体],
        [app/agent/, knowledge/],
        [构造运行证据、上下文包、工具调用和一致性校验，约束教学解释不越过诊断事实。],
      ),
      ([前端 API], [src/api/pipeline.ts, src/api/agent.ts], [封装前端对后端流水线和智能体接口的调用。]),
      (
        [演示页面],
        [src/features/demo/DemoPage.tsx],
        [组织单工位演示主流程，包括图片上传、流水线运行、结果展示和问答交互。],
      ),
      ([可视化组件], [src/components/BreadboardView.tsx], [展示面包板孔位、元件、网络和错误高亮，使诊断证据可视化。]),
      ([网表展示], [src/components/NetlistView.tsx], [展示结构化网表、元件引脚与网络连接关系。]),
      ([阶段时间线], [src/components/StageTimeline.tsx], [展示 S1 至 S5 各阶段执行状态、耗时和中间结果。]),
      ([类型与工具], [src/types/, src/utils/], [定义前后端共享数据结构，并提供面包板、文件、端口标注和结果转换工具。]),
      ([测试程序], [tests/], [保存单元测试、回归样例和流水线 smoke tests，用于验证关键模块行为。]),
    ),
  ),
  caption: [LabGuardian 主要程序清单],
)

#block[
  #set par(first-line-indent: (amount: 2em, all: true), leading: 1em)
  运行时，用户在前端上传面包板俯视图并选择参考电路，后端流水线依次完成元件检测、引脚检测、孔位映射、网表重构、确定性图比对和教学解释生成。部署到 Intel DK-2500 平台时，视觉推理主要运行于 NPU，教学解释模型运行于 iGPU，图比对、检索、调度和证据校验运行于 CPU，从而实现弱网络或离线课堂环境下的本地诊断与解释。

  *附录 B　源代码附件下载链接.* 本作品源代码附件文件为 #link("LabGuardian_Source_Code.zip")[#text(font: 英文字体)[LabGuardian_Source_Code.zip]]，与本报告 PDF 放置在同一提交目录下。附件包含 #text(font: 英文字体)[LabGuardian-Server/] 后端源码、#text(font: 英文字体)[LabGuardian-web/] 前端源码、项目 README、配置示例、知识库、测试程序和必要部署脚本；不包含本地虚拟环境、依赖缓存、运行日志、上传缓存、个人密钥和真实环境变量。
]


#heading(level: 1, numbering: none)[谢辞]

在本报告完成之际，谨向在项目研究与报告撰写过程中给予悉心指导的指导教师，以及给予帮助与支持的队友、同学与提供竞赛平台与技术支持的英特尔公司表示衷心的感谢。
