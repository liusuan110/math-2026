# 如何并入当前 ICRCV 稿件

## 与现有主线的关系

当前 `main.tex` 的标题级贡献是元件条件化引脚姿态估计、单应性校正、几何约束 Snap-to-Grid 和孔位歧义保留。本次审计应作为该主线的真实案例证据，而不是把论文改写成 Agent、电路教学或端到端故障诊断论文。

最适合使用本批材料的位置是 `Qualitative Analysis`、`Limitations and Evaluation Protocol`，以及 Fig. 3 的歧义讨论附近。

## 可以吸收的三个观察

1. **元件计数完整仍不保证孔位确定。** 三张标准场景的元件类别/数量均完整，但歧义引脚比例为 25.0%–40.0%。这直接支持“保留歧义而不是强制最近邻决定”的设计。
2. **真实变体的薄弱点具有结构后果。** 六张姿态/拍摄变体都漏掉至少一根导线；部分旋转图还漏 IC 或竖直电阻。短导线漏检会改变连通分量，适合用来解释视觉误差如何传播到拓扑，而不是宣称这些 S4 报错都是真实故障。
3. **低置信类别混淆需要门控。** `err_amp2_portrait` 中一个电阻以 0.301 置信度被预测为电位器。由于器件类别决定引脚模式和拓扑语义，低置信分类应进入复核/拒识路径。

## 建议加入正文的克制表述

> A diagnostic audit on nine real breadboard images further illustrates why component-level success is insufficient for auditable reconstruction. In three standard-view cases, the expected component classes and counts were recovered, while 25.0%--40.0% of the reconstructed terminals were still flagged as ambiguous by the geometric mapper. Across six pose or capture variants, every case missed at least one thin jumper, and selected rotations additionally missed an IC or a vertical resistor. These convenience cases are not used as an accuracy benchmark; they expose representative failure modes that motivate ambiguity preservation, class-aware confidence gating, and stage-wise evaluation.

如果篇幅不足，可只保留前两句，并把完整九例表放到补充材料或项目归档。

## 不应写入当前稿件的内容

- 不要用 `3/3` 或 `0/6` 报总体准确率；这不是冻结随机测试集。
- 不要把 S4 的全部错误视为真实接线错误；缺少逐针孔位和拓扑真值。
- 不要把本次三端口校正写成论文的主要贡献；它仅证明语义标注能够改善下游比较且不会绕过结构校验。
- 不要把现有标题和摘要主线改为 LLM/Agent 或“全自动诊断”。
- 不要声称旋转是唯一原因；尺度、对比度、遮挡和导线外观同时变化。

## 正式实验如何承接

下一轮应按实体面包板分组构造冻结测试集，补齐元件框、关键点、真实孔位和逻辑网络标注；然后固定相同图片做 S1/S2/S3 oracle 替换与几何消融，报告 PCK、孔位准确率、歧义拒绝精度和 coverage。这样本次案例能从“发现问题”自然过渡到论文的定量实验协议。
