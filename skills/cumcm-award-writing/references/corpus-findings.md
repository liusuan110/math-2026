# Local award-paper corpus findings

## Scope and evidence levels

This guidance was distilled in September 2026 from the local `math-2026-main` workspace. Award labels generally come from repository names and author README files; they were not independently authenticated. Treat them as evidence tiers, not ground truth.

The core sample included:

- self-reported national first prizes: 2020 B desert game, 2023 A heliostat, 2024 A bench dragon, 2025 B SiC thickness;
- national second or provincial first prizes: 2023 B multibeam, 2025 A UAV smoke, 2025 C NIPT;
- provincial second prizes as contrast: 2023 C vegetable pricing, 2024 C crop planning;
- archived “优秀论文” across 2019, 2021, and four 2022 A papers;
- the team's 2022 A practice paper as a comparison, not as award evidence.

Some PDFs are scanned or have non-extractable fonts. Quantitative phrase analysis therefore used only files with reliable extraction or available LaTeX sources; representative pages of key scanned papers were visually reviewed.

## What was stable across stronger papers

1. **Specificity beats elegance.** Strong passages name the actual geometry, state, threshold, search interval, physical mechanism, or decision variable. Their language may be imperfect, but the reader can reconstruct the decision.
2. **The analysis section is operational.** It usually says what makes the problem hard, how the team reduces that difficulty, and what will be computed next.
3. **Models are built in layers.** A baseline mechanism appears first; added variables or constraints are introduced when a later problem requires them.
4. **Results are decision-facing.** Important values, feasible bounds, collision conditions, thresholds, and optimum locations appear near the relevant model rather than only in the conclusion.
5. **Useful assumptions are checked later.** The 2024 A bench-dragon paper, for example, narrows the collision search using a geometric hypothesis and then argues why the hypothesis is valid.
6. **First person is normal.** Many successful papers use “我们” freely to mark choices. Avoiding first person does not make a paper more academic.

## What was not stable

No single surface style predicted award level. Award-labeled papers contained:

- very long or very short abstracts;
- both “本文” and “我们” voices;
- strong and weak typography;
- occasional typos, repetitive restatement, generic model evaluations, and textbook algorithm explanations;
- both polished and noticeably formulaic/AI-like prose.

Therefore do not learn a universal sentence template from the corpus. The award signal lies more in problem-specific reasoning and evidence than in verbal smoothness.

## Descriptive comparison with the team's 2022 A practice paper

Phrase rates below are per 10,000 extracted Chinese characters and are descriptive only:

| Signal | Team 2022 A | Pattern in reliably extracted award samples |
|---|---:|---|
| “我们” | 0.00 | Common; several samples used it frequently |
| “本文” | 17.14 | Highly variable, roughly 0.9-39.9 |
| “因此” | 16.07 | Higher than most sampled papers |
| “进一步” | 7.50 | Higher than most sampled papers |
| “验证” | 16.07 | At the high end, though one provincial-first sample was higher |
| “机器精度” | 3.21 | Absent from the comparison samples |

The team's paper is more technically polished than several award-labeled papers, but its voice is unusually uniform and impersonal. The main issue is not sentence length. It is the combination of:

- no visible first-person decisions;
- repeated validation language across questions;
- frequent “严格、完整、独立、自洽、机器精度” self-certification;
- near-identical subsection rhythm;
- an abstract that reports many states but gives little space to the decisive modeling judgments.

Retain its strengths: exact quantities, energy-based derivation, reproducible checks, and physical range tests. Rewrite first the abstract, problem-analysis paragraphs, figure commentary, model evaluation, and conclusion.

## Weak patterns found even in winning papers

Filter these rather than copying them:

- full restatement of the prompt;
- generic introductions about importance;
- an algorithm's textbook metaphor or history;
- calling a fit “excellent” when the reported out-of-sample metric is weak;
- claiming “significance, robustness, transferability” without separate evidence for each;
- listing many fashionable model names without explaining why each is necessary;
- conclusions ending in generic social or industrial value.

## Interpretation

An award paper does not need literary warmth. It needs visible authorship: concrete choices, causal reasoning, measured evidence, honest limits, and a structure that lets a judge recover the main line quickly. “Removing AI flavor” should mean restoring those functions, not adding colloquial words or random imperfections.

