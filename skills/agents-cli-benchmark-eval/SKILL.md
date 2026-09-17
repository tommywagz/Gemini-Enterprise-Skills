---
name: agents-cli-benchmark-eval
description: "Designs, runs, and scores local evaluation datasets against an ADK agent or command, computes exact-match, token-overlap (ROUGE-like), semantic-similarity proxy, rubric scores, and routing precision/recall, then writes JUnit XML and Markdown reports. TRIGGER when users ask to 'run evaluation datasets', 'evaluate agent accuracy', 'calculate trigger precision/recall', 'generate a JUnit test report for my agent', 'set up an agent benchmark suite', or score an ADK agent locally. DO NOT TRIGGER for live production load testing, training/fine-tuning a model, or general unit tests without an agent output/dataset evaluation objective."
version: 1.0.0
author: Actual Agentic Solutions
tags: [agents-cli, adk, evaluation, benchmark, junit, metrics, safety]
license: Apache-2.0
compatibility: "Python 3.9+; standard library only for scripts/run_eval_and_score.py; an optional local command that accepts a prompt on stdin and writes one response to stdout"
metadata: {}
---

- Local Dataset Evaluator

- Overview
This skill creates repeatable, local evidence for an agent's behavior rather
than treating one successful chat as an evaluation. It evaluates versioned
JSON datasets, runs an optional local agent command without shell expansion,
scores deterministic assertions and output metrics, and emits both JUnit XML
for CI and a Markdown report for reviewers. It is designed for ADK agents but
does not depend on ADK: the runner only needs a command that reads each prompt
from standard input and returns its answer on standard output.

- Prerequisites
- A local JSON evaluation dataset conforming to
  `assets/eval_dataset_schema.json`.
- Python 3.9+ for `scripts/run_eval_and_score.py`; no packages are installed.
- For execution mode, a reviewed local command expressed after `--command`
   that reads one prompt from stdin and writes one response to stdout. Do not
   pass a shell pipeline, API key, or production endpoint.
- **Data classification: Confidential.** Evaluation datasets, agent outputs,
  command stderr, and generated reports can contain customer prompts or
  secrets; redact them before sharing and do not commit sensitive fixtures.

- Workflow

- Step 1: Define the evaluation contract
Copy the schema's minimum fields: unique `id`, `prompt`, `expected`, and one
or more `assertions`. Use `expected_route` for trigger/anti-trigger cases.
Read `references/adversarial_testing_strategies.md` before writing routing
cases; the negative set must contain realistic adjacent requests, not easy
unrelated phrases. Label any test that can create external effects as
`side_effect_risk: "high"` and run it only against a fake/sandboxed tool.

- Step 2: Choose metrics before seeing results
Read `references/eval_metrics_guide.md`. Use exact match for normalized,
closed answers; use token-overlap as a transparent ROUGE-like proxy for
bounded natural-language answers; use an independently reviewed rubric for
qualitative quality. Do not report BLEU/ROUGE/semantic similarity as though a
stdlib approximation were the official library implementation.

- Step 3: Run the dataset
For a precomputed-output dataset (no agent execution):
```
scripts/run_eval_and_score.py --dataset evals.json --junit-out junit.xml --report-out report.md
```
For a local agent command, use `--command` followed by an argv array:
```
scripts/run_eval_and_score.py --dataset evals.json --command python3 agent.py --junit-out junit.xml --report-out report.md
```
The script uses `subprocess.run(..., shell=False)`, limits each case with
`--timeout-seconds`, and never sends inputs to a remote service. If the agent
requires network, credentials, or makes mutations, stop and obtain a
sandbox/mock implementation before evaluating.

- Step 4: Interpret failures by assertion type
- `exact_match`, `contains`, or `not_contains` failures are deterministic
  regressions; fix the agent or expected contract before changing thresholds.
- `route` failures feed the confusion matrix. For a trigger route: recall is
  `TP / (TP + FN)`; for an anti-trigger route: false-positive rate is
  `FP / (FP + TN)`. Do not call an empty anti-trigger set "100% precision".
- `min_token_overlap` or `min_semantic_similarity_proxy` failures are signals
  for human review, not proof that an answer is factually wrong. Add a rubric
  assertion if factual completeness matters.
- Command timeout/non-zero exit is an ERROR in JUnit, distinct from a failed
  quality assertion.

- Step 5: Gate and report
Use `assets/evaluation_report_template.md` to present the command, dataset
revision/hash, case totals, metric definitions, routing confusion matrix,
failures/errors, and known gaps. Set a release gate explicitly (for example,
no errors, 100% critical assertions, and routing FPR <= 2%); do not infer a
gate from one aggregate score. Attach `junit.xml` to CI so failed cases are
visible as individual test cases.

- Examples

- Example 1: Skill trigger routing
Input: "Does the new evaluator skill fire only for agent benchmarks?"
Expected behavior: create balanced positive `expected_route: true` and
adjacent anti-trigger `expected_route: false` cases, add `route` assertions,
run the script, and report TP/FP/TN/FN with precision, recall, and FPR.

- Example 2: Local ADK command regression suite
Input: "Run our ADK agent over 50 golden prompts and produce JUnit."
Expected behavior: require a command that accepts stdin and uses sandboxed
tools, invoke it with `--command`, classify command failures as JUnit errors,
and return the report plus per-case XML results.

- Error Handling
- Dataset fails schema/JSON parsing: do not execute any command; correct the
  indicated case ID/field and rerun.
- A command returns non-zero or exceeds the timeout: record an ERROR, preserve
  stderr only in the local Markdown report after redaction, and do not treat
  it as a failed correctness assertion.
- A case has no precomputed `actual` and `--command` is absent: record an
  ERROR rather than fabricating an agent output.
- Never place credentials or private production prompts in datasets, command
   arguments, JUnit properties, or reports. Redact output before sharing.
- A referenced metric or adversarial-testing guide is unavailable: do not
   invent a threshold or safety procedure. Stop and obtain the versioned
   reference before defining or running the affected cases.

- Reference Files
- **references/eval_metrics_guide.md**: formulae, threshold guidance, and
  rubric design; read in Step 2.
- **references/adversarial_testing_strategies.md**: balanced trigger and
  anti-trigger design, mutation testing, and safety cases; read in Step 1.
- **scripts/run_eval_and_score.py**: local dataset runner, scorer, JUnit XML,
  and Markdown report generator; run in Step 3.
- **assets/eval_dataset_schema.json**: Draft 2020-12 dataset contract.
- **assets/evaluation_report_template.md**: report layout for Step 5.

- Output Format
Return (1) the command and dataset path, (2) case/pass/fail/error totals,
(3) metric definitions and values, including a routing confusion matrix when
applicable, (4) paths to JUnit XML and Markdown reports, and (5) the explicit
release-gate decision plus remaining test coverage gaps.
