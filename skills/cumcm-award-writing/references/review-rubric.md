# CUMCM paper review rubric

Use the rubric for editorial diagnosis. It does not predict an award.

## Priority levels

- **P0 - submission or truth risk:** fabricated/unsupported data, wrong units, inconsistent results, missing source, non-reproducible program, identity leak, or current-rule violation.
- **P1 - award-critical:** reasoning gap, unjustified model choice, hidden core contribution, overclaim, invalid validation, or conclusion not supported by results.
- **P2 - judge-friction:** redundancy, long restatement, textbook filler, weak figure explanation, inconsistent terminology, or excessive precision.
- **P3 - polish:** punctuation, typography, isolated awkward phrases, and minor visual inconsistency.

## Six review dimensions

Score each from 0 to 4 and explain the evidence.

1. **Problem understanding:** the paper identifies the real obstacle and the relationship among subproblems.
2. **Decision traceability:** important assumptions, variables, models, and solver choices have stated reasons.
3. **Evidence chain:** major claims link to equations, data, tables, figures, comparisons, or tests.
4. **Claim calibration:** wording matches the strength and scope of the evidence.
5. **Judge readability:** abstract, headings, captions, and paragraph openings expose the main line quickly.
6. **Authorial voice:** local choices and uncertainty are visible; generic transitions and self-praise do not dominate.

Do not average these into a fake award probability. A single P0 or major P1 can dominate the outcome.

## Section checks

### Abstract

- Can a judge recover the method and main result for each problem?
- Are the memorable contributions visible within one reading?
- Are there too many routine numbers or too few decision-relevant numbers?
- Does the abstract claim more than the body demonstrates?

### Problem analysis

- Does each subsection name a genuine difficulty?
- Is the method motivated by that difficulty rather than merely announced?
- Are alternatives or simplifications explained where they matter?

### Modeling

- Are coordinates, variables, assumptions, objectives, and constraints interpretable?
- Are formulas connected by prose that explains purpose and consequence?
- Is standard algorithm background longer than the paper-specific modification?

### Results

- Does each key figure/table support a nearby claim?
- Are comparison, mechanism, uncertainty, and feasibility discussed?
- Do numbers agree across abstract, body, figures, tables, conclusion, and attachments?

### Validation

- Does each test address a plausible failure mode?
- Are perturbation ranges, baselines, and response metrics stated?
- Is “稳健/准确/有效” earned by evidence?

### Conclusion

- Does it synthesize findings rather than copy the abstract?
- Are limitations concrete enough to change interpretation or future use?

## AI-like prose diagnostic

Treat these as signals for manual inspection, not proof of AI authorship:

- parallel subsections with nearly identical sentence skeletons;
- repeated “本文/进一步/因此/验证” without local content;
- every paragraph ends in a benefit claim;
- dense chains of abstract nouns and paired adjectives;
- no first-person decisions, rejected alternatives, surprises, or uncertainty;
- claims of machine precision or global optimality repeated more often than the evidence requires.

For every flagged passage, identify the missing rhetorical function: reason, evidence, mechanism, limitation, or decision. Rewrite the function, not merely the vocabulary.

## Three-member defense test

Before finalizing, randomly assign each team member passages they did not write. For every sampled equation, figure, parameter, and conclusion, the member should be able to explain:

1. where it came from;
2. why it is needed;
3. how it was computed or verified;
4. what would make it fail.

Re-derive, re-run, narrow, or remove anything the team cannot defend.

