# Award-oriented CUMCM writing guide

This guide describes rhetorical functions that recur in strong papers. It is not a fixed template. Preserve the problem's natural structure.

## 1. Abstract

The abstract is a decision-and-result map, not a compressed copy of the whole paper.

Use this order when it fits:

1. State the overall modeling object and the unifying idea in one or two sentences.
2. For each problem, give the problem-specific obstacle, the chosen model or computation, and the main result or judgment.
3. End with one cross-problem insight or one concrete validation result.

Keep numbers that help distinguish solutions: an optimum, error, improvement, threshold, or final policy. Remove long state vectors, routine solver tolerances, and exhaustive intermediate outputs unless the problem explicitly asks for them.

Bad ending:

> 模型精度高、稳定性强，可为相关领域提供科学依据。

Better pattern:

> 将采样间隔减半后，最优功率变化 0.03%；在参数扰动 5% 内，最优阻尼始终位于同一区间。

Bold type may help a dense abstract, but use it only for the few methods and results a judge should remember.

## 2. Problem restatement and analysis

Restatement records the tasks and their relationship. It should not paraphrase every sentence of the prompt.

Problem analysis must answer three questions:

- What is the actual obstacle?
- Which modeling decision resolves it?
- What evidence will show that the decision worked?

Strong analysis is problem-specific:

> 直接穷举全部补给策略计算量过大，但天气已知时状态转移只依赖当天位置、库存和资金。因此将完整策略拆成按天递推的子问题，并对不可行库存状态提前剪枝。

Weak analysis merely announces tools:

> 本问题较为复杂，因此采用动态规划、机器学习和智能优化算法综合求解。

When making a simplification, state both the benefit and the later check. A useful pattern is “先作假设 - 缩小搜索或降低维度 - 随后证明或数值核验假设成立”.

## 3. Model construction

Organize derivations around decisions, not around a textbook chapter.

- Introduce coordinates, states, or decision variables only when they become necessary.
- Explain the physical, statistical, or operational meaning of the objective and each non-obvious constraint.
- After a formula, interpret the terms that matter to the model; do not restate obvious algebra.
- Explain modifications to a standard method. A generic history of PSO, entropy weight, ARIMA, or neural networks rarely earns space.
- If two methods are possible, state the decisive tradeoff: data size, nonlinearity, globality, interpretability, time, or available constraints.

Prefer a compact chain:

> observation -> modeling choice -> mathematical expression -> solver -> verification.

Avoid a catalog:

> definition -> generic algorithm principle -> long step list -> unexplained output.

## 4. Results and figures

Every important result paragraph should perform at least two of these jobs:

- state the result;
- compare it with a baseline, boundary, or alternative;
- explain the mechanism;
- connect it to the requested decision;
- state its valid range or uncertainty.

Use “由图可见” only when the next words identify a precise visual feature. Do not write “趋势良好” without naming the direction, interval, turning point, or magnitude.

Calibrate claims to metrics. For example, a low out-of-sample `R^2` cannot be called “拟合表现优异” merely because the curve looks aligned. Distinguish statistical significance, predictive value, physical plausibility, and numerical convergence.

Figures should be readable without hunting through prose:

- consistent Chinese/English terminology;
- units on axes and table columns;
- caption states what is compared;
- legends use the same names as the text;
- annotations highlight the optimum, threshold, or feasible boundary when relevant.

## 5. Validation and sensitivity

Validation is evidence, not a ritual section. Select checks that address the model's actual failure modes:

- numerical convergence for integration or optimization;
- residual structure or out-of-sample performance for statistical models;
- feasibility and conservation checks for physical models;
- baseline or alternative method comparison;
- perturbations of assumptions that could change the decision.

State the perturbation and measured response. Do not repeat “验证模型稳健” after every question. One well-designed table can replace several paragraphs of self-certification.

## 6. Conclusion and evaluation

The conclusion should recover the decision chain, not reproduce the abstract. Lead with what was learned, then give only the results needed to support that learning.

Model limitations should identify a mechanism and its consequence:

> 附加质量被视为定常参数；在宽频不规则波下，它随频率变化，当前最优阻尼因此不能直接外推。

Avoid generic advantages such as “结构清晰、适用范围广、精度较高”. If a strength has no comparison or evidence, omit it.

## 7. Authorial voice without colloquialization

“Human” prose is not casual prose. It shows local judgment.

Use first person selectively:

- “我们取稳定后的单周期作为统计窗口，因为……”
- “比较两种口径后，我们保留……”
- “这一结果与预期相反，原因在于……”

Vary paragraph and sentence length naturally. A paper in which every question has identical paragraph counts and identical transitions feels generated even when each sentence is grammatical.

High-risk generic markers include dense repetition of:

- “本文针对……建立……并验证……”;
- “首先、其次、最后” in every subsection;
- “进一步、综合来看、从多个维度” without new reasoning;
- “准确性、有效性、稳健性、可迁移性” without measurements;
- “具有重要意义、提供理论依据” as a default ending.

Do not ban individual words. Diagnose repetition and lack of evidence in context.

