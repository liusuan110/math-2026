# LabGuardian — ICRCV 2026 论文交接文档

更新时间：2026-08-17（Asia/Shanghai）

## 0. 稿件形态变更（2026-08-17）

正式稿件已从 Typst 迁移到会议官方 IEEE 模板：

- 主文件：`main.tex`（`\documentclass[conference]{IEEEtran}`），编译产物 `main.pdf`，**6 页，无 overfull box**。
- 编译：`pdflatex main.tex && pdflatex main.tex`；`IEEEtran.cls` 已复制到根目录，本机 TeX Live basic 不含该类，也不含 `IEEEtran.bst`，因此参考文献直接写在 `thebibliography` 中。
- 正文已去除全部竞赛元素：不再出现赛事名称、"作品/参赛/评委"、原创性声明、致谢中的赛事方、源码附件清单，硬件表述改为 "an edge platform built around an Intel Core Ultra 5 225U" 而非赛事开发板型号。
- 论文口吻改写：教学场景不再作为卖点，改为"手工布线硬件的自动检查 / 机器人装配核验"这类中性动机；教学解释小模型降为 "Cost of the Auditable Interface" 一小节的部署开销，明确声明不属于视觉主张。
- 插图全部改为英文：`figures/en/`（由 `tools/make_figures.py` 生成），原 `figures/cadx/*.pdf` 含中文标注，仅作素材保留。功率图从 `source-material/board_data/yolo_power_*.{csv,json}` 重绘（注意 CSV 的 `t_s` 列比真实时间大 2 倍，脚本按 phase 日志重建时间轴，与原绘图脚本一致）。
- `main.typ` 保留为历史版本，不再维护。

收尾修改（同日）：

- 三位作者改为同一行（机构名手工断成两行以适配 IEEE 三栏作者块）；"*Corresponding author" 改为标题 `\thanks` 脚注。
- **插图清晰度修复**：此前 matplotlib 以默认 100 dpi 保存，1849 px 的面板被重采样到约 185 px，这是照片发虚的真实原因。现固定 `RASTER_DPI=800`（源 PDF 栅格化）与 `SAVE_DPI=600`（保存），面板输出 1100×1041 px @600 ppi，已达嵌入原图的原生分辨率（964 px），并加了轻度 UnsharpMask 与对比度补偿。**不要把这两个 dpi 调回默认**，否则清晰度立刻退回。若投稿系统限制体积（当前 `main.pdf` 5.0 MB），把 `SAVE_DPI` 降到 450 即可，仍高于印刷所需。
- Fig. 3、Fig. 5 的中文残留已按栅格坐标实测位置精确遮盖并改写英文标注；`pdftotext main.pdf` 扫描确认全文 0 个 CJK 字符。
- 第 V 节改写：把"我们的实验日志缺少逐关键点预测与孔位标签"改为范围声明（几何环节本文定性评估，定量孔位基准需要现有标注不含的逐引脚孔位标签，随后给出固定协议），去掉"camera-ready 前补上"这类承诺。

插图与语言二轮（同日）：

- **Fig. 5 面板 (b) 已重绘**：不再裁剪原项目的渲染图，改为在 `tools/make_figures.py` 里按流水线自己导出的拓扑级 SPICE 网表（`R1 N0 N6 / R2 N6 0 / R3 N5 N3 / R4 N1 0 / R5 N3 N7 / R6 N6 N4 / XIC1 N4 N3 N1 VEE NC N2 N0 VCC DIP8`）重画，图与网表不会再各说各话。布局是手工定的平面嵌入：IC 的邻居按引脚序排在中枢周围，只有 R2、R6 走外圈并画成三次贝塞尔曲线，全图无交叉。
- 同时修正一处**事实性表述**：原文与原图说"非导线元件都是边"，但 DIP-8 跨 3 个以上网络，不可能是二端边——正文与图例现在写成"二端元件是边，跨两个以上网络的封装保留为自身节点并标注引脚号"。
- 网络计数口径澄清：项目原图题注写"10 网络"，而 SPICE 导出里有 11 个网名；差异来自 GND 在 SPICE 中导为节点 0 不计入命名网络。正文与题注统一写作"十个命名网络加接地参考"。
- 通讯邮箱改为 `liusuan@bupt.edu.cn`。
- 语言润色：术语统一（net/node、pin/terminal 在方法一节给了明确定义），去掉未定义的 "the mapper"，拆分过长句，若干处改为标准学术表述。

插图三轮 —— Fig. 5 的绘制质量（同日）：

- 二端元件不再用"白底方框写 R1"的流程图画法，改为在边上内联绘制 **IEC 电阻符号**，位号用数学斜体（`$R_1$`）标在符号外侧；曲线边上的符号按贝塞尔切线角旋转（`_bezier()` 同时返回点与切角）。
- **DIP 封装**改为真实封装形态：定向缺口（`Wedge`）、8 个实心焊盘、盘内引脚编号。
- 配色由单一灰改为**有语义的双色调**：信号网浅蓝（`#EDF3FA`/`#2E5E8C`）、供电网浅琥珀（`#FBF0DF`/`#A9762E`）、地网中性灰并附**标准接地符号**；元件与连线保持中性深灰，全图只有两个彩色相位，印刷与黑白复印都不糊。
- 网络名改为数学下标排版（`$N_0$`、`$V_{CC}$`、`$V_{EE}$`），`mathtext.fontset` 设为 `stix` 以匹配正文 Times。
- 图例改为手绘（`_legend()`），含真实符号而非 matplotlib 代理图元。
- Fig. 2 图例与方法一节的 pin/terminal 定义对齐：`component node` → `component instance`，`component-to-pin link` → `terminal association`（后者同时是为了不被图例栏宽截断）。
- **图向与实物对齐**：封装改为横放（引脚上下两排跨中间沟槽，与照片里 DIP 的实际姿态一致），$V_{CC}$ 在上、GND 在下。注意这不是把原图刚性旋转 90°——刚性旋转会把 $V_{CC}$ 甩到左侧、GND 甩到右下，反而丢掉"电源在上、地在下"这条同样来自实物的对应；因此是按新的平面嵌入重排：邻居仍按引脚序绕封装排列，只有 R1、R2 走外圈曲线，全图无交叉。图幅随之从 2.95 in 提高到 3.45 in（`width_ratios` 改为 [1, 1.12]），panel (a) 也因此变大、网络标签更清楚。
- **视觉语言改为对标 arXiv:2504.10240（GNN-ACLP，模拟电路链路预测）**，即用户报告原本参考的绘图风格：底层粗浅灰连线（`WIRE_LW=2.0`，round cap）、上层实心饱和节点配白色标签（信号网violet `#5B4B8A`、供电网amber `#C0642A`、地slate `#3A4750`）、元件统一用红色系 `#A8323C`（电阻符号描边、位号、DIP 轮廓与焊盘）。删掉图例框，编码信息移入题注——该文的图也是无图例、靠题注说明。

插图四轮 —— 连线走线与一处重建错误（同日）：

- **连线改为正交走线**：外圈的 $R_1$、$R_2$ 不再用自由弧线，改成直线段 + 转角小圆弧（`_polyline()`，`CORNER_R=0.38`，Path 的 CURVE3 做圆角）；$R_2$ 从右侧进入 GND，避开下方的接地符号。封装扇出的短连线保留直线斜连。
- **⚠️ 发现一处真实的重建错误，投稿前必须处理**：照片里蓝色跳线 W2 的下端与 R5 右引脚在**同一条 5 孔导通带**上，物理上 N2 与 N7 应是同一网络；但导出的网表里两者是独立网络（`R5 N3 N7`，IC pin6→N2，中间无元件），即 **union-find 漏合并**。
  - 证据：在 `figures/en/_raster/netlist_info-1.png` 上标定孔位栅格（列距 ≈179 px），R5 右引脚 x=441 → 落在第 2 列（列心 422，在孔上）；跳线下端标记 x≈508 → (508−64)/179 = **2.48，正好卡在第 2、3 列中间**，被吸附到了隔壁列。这正是论文 III-D 描述的孔级歧义失效模式的真实样本。
  - 后果：Fig. 5 目前展示的是一份**漏掉一条连接**的网表，题注却按成功案例叙述。审稿人对照 (a)(b) 有可能看出来。
  - 三个处理选项：①（推荐）Windows 端对该孔位做一次人工确认后重跑并重新导出网表，N2/N7 合并，顺带演示闭环修正；②换一块导出本身正确的板子做这张图；③保留现状但在题注里点明这处漏合并，当作 Fig. 3 歧义问题的真实后果——诚实但会削弱"输出足以被符号层消费"的论述。
  - **在做出选择前，不要把跳线画成 N2–N7 的边**：那会让图与其声明的数据来源（导出网表）不一致，等于在图上把系统没做对的结果画对。

Fig. 5 换板重做（同日，第五轮）：

- **换成 `反向放大器-2` 这块板**，并且**在本机真跑了一次完整链路**（`LabGuardian-Server` 的离线入口 `scripts/manual/tools/vision/run_official_pipeline_debug.py`），不是从旧渲染图裁的。运行方式（`.env` 里的 Windows 路径与 CUDA 设备需要覆盖）：

```bash
cd /Users/liusuan/Desktop/LabGuardian-Server && \
YOLO_MODEL_PATH=train_demo/merged_det_v2/weights/best.pt \
PIN_MODEL_PATH=train_demo/pose_components/weights/best.pt \
YOLO_OBB_MODEL_PATH="" YOLO_DEVICE=cpu PIN_MODEL_DEVICE=cpu \
.venv/bin/python scripts/manual/tools/vision/run_official_pipeline_debug.py \
  --images /Users/liusuan/Desktop/image-1/反向放大器-2.jpg --output-root /tmp/lg_run
```

- 运行结果与照片已收入 `source-material/board_run/`（`inverting_amp_pipeline_result.json` + `inverting_amp_board.jpg`），**Fig. 5 两栏都由这一份 JSON 生成**：panel (a) 是照片叠加（元件框 + 引脚点按网络着色 + 同网络最小生成树连线 + 歧义引脚红色虚线环），panel (b) 是 `netlist_v2` 的元件—网络图，两栏共用同一套每网络配色，可按颜色对照。
- 该次运行的事实：12 元件（6 电阻 / 5 跳线 / 1 DIP-8）、30 引脚、10 网络、**6 个引脚被系统自己标为 ambiguous**；耗时 detect 788 ms + pose 1298 ms + mapping 29 ms + topology 2 ms（本机 CPU）。IC 引脚 1/5/8 落在单引脚节点上按未连接报出（µA741 的 1/5 为调零脚、8 为 NC，与器件本身一致）。
- **需要你确认的一点**：本次重建里 IC pin6（输出）落在 role=GND 的 NET_010 上，而 R2 的另一端 NET_007 是悬空单引脚网络。这块板若是**故意接错的故障样例**，题注可以点明并成为诊断用例；若它本应是正确电路，则说明这次重建有错，需要复核。目前正文与题注只陈述"恢复出的结构"，没有声称电路正确。
- 前一块板（board_1）那处 N2/N7 漏合并的问题随本次换图一并退出正文，但结论仍然成立，记录在上一节。
- `main.pdf` 体积升至 7.0 MB（新照片 600 ppi）。若投稿系统限体积，把 `SAVE_DPI` 降到 450 可回到 5 MB 量级。

**投稿前必须补的两处 TODO（已在 `main.tex` 中以注释标出）**：第二、三作者的机构邮箱或 ORCID；数据集训练/验证/测试各划分的图像数、实例数与关键点数。

## 0.5 投稿与注册流程要点（2026-08-17 从官网核实）

- 投稿系统：`zmeeting.org/submission/icrcv2026`，或邮件 `icrcv_conf@163.com`；**单盲**评审（保留作者信息）；**禁止一稿多投**。
- 注册费（作者档）：非会员 4000 CNY；**学生 3550 CNY**（仅按第一作者是否学生判定，注册时需附学生证复印件）；IEEE 学生会员 3300 CNY。**一次注册含 6 页，本稿正好 6 页，无超页费。**
- 注册需发三样到 `icrcv_conf@163.com`：终稿、填好的注册表、付款凭证；每篇录用论文至少一位作者必须预注册。
- **退款政策**：会前 60 天以上退 70%，30–60 天退 50%，30 天内不退。会议 11/6，注册截止 10/5 已落在 30–60 天档 → **缴费后最多只能退一半，务必先确认经费与发票抬头再付**。
- 报告形式：2026 页面未提线上报告；但官网往届页面记载 **ICRCV 2025 为 hybrid（onsite + online）**，优秀报告分 Onsite/Online 两类。线上报告需向秘书处书面确认。
- 关键日期：投稿 9/1，通知 9/20，注册 10/5，会议 11/6–8（南理工江阴校区），最终日程 10 月中旬发布。

## 1. 当前稿件

- 题目：**LabGuardian: Geometry-Constrained Pin Pose Estimation for Visual Breadboard Reconstruction**
- 第一作者：**Su'an Liu**
- 第二作者：Xinran Zhang
- 第三作者：Jiali Ruan
- 当前篇幅：6 页，包含图、表和参考文献。
- 摘要：171 词，低于 200 词限制。
- 当前定位：以计算机视觉为主，核心贡献为元件条件化的引脚姿态估计、平面单应变换、几何约束 Snap-to-Grid 与歧义保留机制。
- 次要内容：CPU/iGPU/NPU 部署数据、功耗、SPICE/VF2 和 INT4 解释模块仅作为系统证据，不作为主要学术贡献。

## 2. 目标会议信息

| 项目 | 当前官网信息 |
|---|---|
| 会议 | 2026 8th International Conference on Robotics and Computer Vision (ICRCV 2026) |
| 日期 | 2026 年 11 月 6–8 日 |
| 地点 | 南京理工大学江阴校区，江苏江阴 |
| 投稿截止 | 2026 年 9 月 1 日 |
| 录用通知 | 2026 年 9 月 20 日 |
| 注册截止 | 2026 年 10 月 5 日 |
| 语言 | 英语 |
| 评审 | 单盲评审 |
| 页数 | 全文 4–10 页；常规注册包含最多 6 页，超页收费 |
| 投稿限制 | 禁止一稿多投或同时投稿 |
| 出版声明 | 官网称录用并注册的全文将进入 ICRCV 2026 论文集，计划归档 IEEE Xplore，并提交 EI Compendex、Scopus 等检索 |
| 联系邮箱 | icrcv_conf@163.com |

官网来源（2026-08-17 核对）：

- https://www.icrcv.org/
- https://www.icrcv.org/sub.html
- https://www.icrcv.org/reg.html
- https://www.icrcv.org/chinese.html
- 投稿系统：https://www.zmeeting.org/submission/icrcv2026

注意：IEEE Xplore/EI/Scopus 是会议组织方的出版与送检声明，不应在正式检索完成前表述为已经检索。2026 年是否支持线上参会、远程报告或代讲，官网当前没有明确承诺；如有需求，应在注册前邮件确认。

## 3. 当前论文主线

1. 将面包板图像重建定义为细粒度视觉结构恢复问题，而非通用电路诊断。
2. 将元件端子定位表述为 **Component-Conditioned Top-Down Pose Estimation**。
3. 使用完整图像推理保留长引脚、邻域网格、遮挡关系与封装上下文。
4. 使用 **Homography-Based Spatial Mapping** 将透视视角归一化至标准板平面。
5. 使用 **Geometry-Constrained Snap-to-Grid** 将连续关键点映射到离散孔位，并保留候选排序和拒绝原因。
6. 电气网表、SPICE 和 VF2 仅消费视觉重建结果，不反向提供视觉证据。

## 4. 已保留的主要量化结果

| 指标 | 当前结果 |
|---|---:|
| 元件检测 Precision / Recall | 0.991 / 0.989 |
| 元件检测 mAP50 / mAP50-95 | 0.991 / 0.786 |
| 引脚关键点 Precision / Recall | 0.955 / 0.954 |
| 引脚姿态 mAP50 / mAP50-95 | 0.947 / 0.829 |
| NPU INT8 平均延迟 | 13.37 ms |
| NPU INT8 P99 | 15.61 ms |
| NPU INT8 吞吐率 | 74.7 image/s |
| NPU INT8 包功耗 / 单次能耗 | 8.53 W / 114.2 mJ |
| CPU INT8 包功耗 / 单次能耗 | 26.37 W / 813.6 mJ |
| 确定性视觉到模板链路 | < 100 ms |
| INT4 存储变化 | 3.1 GB → 941.5 MB |
| 量化前后规则通过率 | 80.0% → 80.0%（30 题，小样本） |

## 5. 投稿前最高优先级工作

### P0：必须完成

1. **补几何实验。** 当前尚无可发表的 Homography/Snap-to-Grid 消融，也没有完整的 pin-to-hole assignment accuracy。
2. 至少报告：归一化关键点误差（NKE）、PCK、孔位命中率、歧义拒绝精确率，并按视角与遮挡程度分层。
3. 对比：无单应变换、仅最近邻吸附、完整几何约束三种设置。
4. 补充训练/验证/测试的图像数、元件实例数、关键点数和类别分布。
5. 下载并逐项对照 ICRCV 官方模板。当前稿使用 Typst 的 `@preview/charged-ieee:0.1.4`，版式接近 IEEE，但不能默认等同于会议最终官方模板。

### P1：强烈建议

1. `figures/cadx/` 是项目真实图，应保留；但其中部分嵌入文字仍为中文，投稿前应从原始绘图工程重新导出英文版。
2. 将 `diag_demo.pdf` 仅作为视觉证据可追溯性案例；避免扩写成电气诊断或网表算法的主要贡献。
3. 核查图像使用授权、数据隐私、作者姓名拼写、单位英文名和作者顺序。
4. 通过 IEEE PDF 检查或会议指定检查器确认字体嵌入、页面尺寸和链接。
5. 做一次英语母语风格终审，重点检查 “top-down” 的定义是否与单阶段 YOLO-Pose 实现表述一致。

## 6. 工作区文件说明

- `main.typ`：当前论文主文件，路径已改为相对当前目录，适合 macOS。
- `refs.bib`：当前参考文献数据库。
- `LabGuardian-ICRCV-2026-draft.pdf`：已编译的 6 页稿件。
- `figures/cadx/`：项目专属端到端、歧义、诊断、网表及功耗图。
- `figures/yolo_*.png`：YOLO 全幅检测与关键点定性结果。
- `source-material/final_report_v2.*`：中文长报告及 Typst 源文件。
- `source-material/LabGuardian_Source_Code.zip`：原项目源码归档。
- `source-material/board_data/`：现有实验记录与 CSV 数据。
- `source-material/scripts/`：旧报告图表生成脚本。

## 7. 在 macOS 上继续写作

建议安装 Typst：

```bash
brew install typst
```

在本目录执行：

```bash
typst compile --root . main.typ LabGuardian-ICRCV-2026-draft.pdf
```

首次编译可能需要联网下载 `@preview/charged-ieee:0.1.4`。所有论文资源均应使用相对路径，避免写入 Windows 盘符路径。

## 8. 推荐投稿流程

1. 完成 P0 实验并冻结作者顺序、题目、摘要和数据表。
2. 导入或复刻 ICRCV 官方模板，重新检查 6 页边界。
3. 由指导老师审核论文贡献、实验真实性、作者名单和投稿许可。
4. 在投稿系统创建稿件并填写作者、单位、关键词、摘要及主题方向。
5. 上传 PDF，完成重复率、字体、页数和匿名要求检查；本会为单盲，当前官网允许稿件显示作者信息。
6. 投稿后保存 Paper ID、确认邮件和最终上传 PDF。
7. 录用后完成版权、注册和报告安排；至少一位作者需要完成预注册。

## 9. 当前风险结论

目前稿件已经具有明确的 ICRCV 视觉叙事和可读的六页结构，但几何变换是标题级贡献，却缺少对应的定量消融。这是当前最大的审稿风险，优先级高于继续扩写硬件功耗、VLM 或 SPICE 网表内容。