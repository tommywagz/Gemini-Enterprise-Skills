# Adversarial Evaluation Strategies

## Balanced route datasets

Build positives from the skill's explicit trigger phrases and realistic
paraphrases. Build negatives from the closest neighboring workflows: for an
agent evaluator, include general pytest requests, load tests, model fine-
counts, otherwise a mostly-negative dataset can conceal poor recall.

## Mutations and boundaries

Create minimal pairs: change only one phrase that should reverse routing.
Test abbreviations, typos, indirect wording, multilingual inputs supported by
fixed regression set; add every production incident as a sanitized case.

## Safety cases

Exercise prompt injection, secret-like strings, unsafe tool requests, and
attempts to override evaluation instructions only in an isolated fixture.
Assert safe refusal or a mock-tool block, never invoke a real payment, email,
file deletion, or external network target. Redact secrets before placing a
failure in JUnit or Markdown artifacts.

## Review discipline

Freeze expected outputs and thresholds before a candidate run. Separate
development and held-out sets. Investigate false positives/negatives by case,
not by aggregate score alone, and avoid repeatedly tuning on the held-out set.
