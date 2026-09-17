# Evaluation Metrics Guide

## Exact and overlap metrics

| Metric | Formula / implementation | Use |
|---|---|---|
| Exact match | normalized actual equals normalized expected | IDs, JSON labels, routes, closed answers |
| Token overlap | `2 * |A intersect B| / (|A| + |B|)` on lowercase word sets | Transparent ROUGE-like regression signal |
| BLEU / ROUGE | N-gram precision / recall families | Use their maintained libraries when these named metrics are required; do not relabel a set-overlap proxy as BLEU or official ROUGE |
| Semantic similarity | Embedding cosine similarity | Use a versioned embedding model and fixed threshold; absent an embedding dependency, the bundled script offers only lexical proxy |

Normalization should be declared: the bundled evaluator trims, case-folds,
and collapses whitespace for exact strings. It does not parse/normalize JSON.

## Routing metrics

For positive/trigger cases, `TP` is a true activation and `FN` is a missed
activation. For negative/anti-trigger cases, `TN` is a correct non-activation
and `FP` is an accidental activation.

```
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
fpr       = FP / (FP + TN)
```

Report `n/a` when a denominator is zero; never replace it with 1.0.

## LLM-as-a-judge rubric

Use a separate, versioned judge model only where deterministic assertions
cannot measure quality. Define atomic criteria (for example correctness,
completeness, citation fidelity, and safe refusal), anchors for scores 1-5,
prompt/response/judge-version evidence subject to privacy policy, and spot
check disagreement with human reviewers. Judge output is an evaluation signal,
not ground truth and not a replacement for adversarial safety tests.
