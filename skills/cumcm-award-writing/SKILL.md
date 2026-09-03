---
name: cumcm-award-writing
description: Analyze, draft, rewrite, and review Chinese CUMCM papers using evidence-backed patterns distilled from award-winning local papers. Use for abstracts, problem analysis, model narratives, results interpretation, conclusions, and diagnosis of generic or AI-like prose. Do not use to invent models, results, citations, or AI-use disclosures.
---

# CUMCM Award Writing

Help the team sound like authors who made and verified modeling decisions. Optimize for clarity, evidential support, and calibrated claims - never for evading AI detection.

## Select the mode

- **Draft:** Turn verified modeling notes, equations, results, and limitations into paper prose.
- **Rewrite:** Preserve every mathematical meaning and number while improving reasoning flow and authorial voice.
- **Review:** Diagnose reasoning, evidence, structure, claim calibration, and generic/AI-like phrasing; prioritize issues by award impact.
- **Corpus analysis:** Compare a user-selected paper set. Run `scripts/analyze_papers.py` for descriptive signals, then visually inspect representative pages. Never treat phrase counts as quality scores or AI detection.

Before drafting or rewriting, identify which facts are verified. Ask for missing facts only when a safe rewrite is impossible; otherwise mark a narrow placeholder instead of inventing content.

## Core writing standard

1. Give each paragraph one job: a modeling decision, its reason, the supporting equation/result, and its implication.
2. Name the problem-specific obstacle before the method. Explain why the chosen method fits that obstacle.
3. Put formulas inside a causal narrative: define why the expression is needed before it, then interpret terms or consequences after it.
4. Report concrete evidence. Replace self-certifying adjectives such as “准确、有效、稳健、严格” with an error, comparison, convergence change, feasibility check, or sensitivity interval.
5. Use “我们” when it identifies a real team decision. Do not force impersonal “本文” constructions throughout the paper.
6. Preserve uncertainty and boundaries. State when an optimum is local, a parameter is assumed, evidence is weak, or a conclusion applies only in a tested range.
7. Prefer direct technical verbs: “取、定义、比较、舍去、约束、代入、得到、发现”. Avoid decorative importance claims and generic transitions.
8. Do not copy distinctive wording from award papers. Transfer rhetorical functions, not sentences.

## Required references

- For any drafting or rewriting task, read [references/award-writing-guide.md](references/award-writing-guide.md).
- For a paper review, also read [references/review-rubric.md](references/review-rubric.md) and use its priority scheme.
- For a new corpus study or when explaining where the guidance came from, read [references/corpus-findings.md](references/corpus-findings.md).

## Drafting constraints

- Never change a value, unit, symbol, model assumption, claimed optimum, sample size, or citation without evidence.
- Do not manufacture model comparisons, sensitivity tests, error rates, “innovation points,” or practical significance.
- Do not add algorithm tutorials unless the mechanism is needed to understand a modification or implementation choice.
- Avoid repeating the same content in problem restatement, problem analysis, section summaries, model evaluation, and conclusion.
- Keep the abstract within the current contest format. If exact compliance matters, verify the latest official CUMCM rules because they change over time.
- AI-use statements must reflect actual use. Never minimize or conceal AI involvement.

## Default review output

Lead with the editorial verdict, then provide:

1. the five highest-impact issues;
2. section-specific findings with quoted excerpts or precise locations;
3. factual gaps or claims that need verification;
4. two or three representative rewrites using only known facts;
5. a short final-pass checklist for the team.

Keep stylistic comments subordinate to mathematical correctness, evidence, and judge readability.
