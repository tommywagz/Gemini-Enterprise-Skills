# Skill Evaluation Report: google-agents-cli-adk-code

**Date:** 2026-08-25
**Evaluator:** evaluator (Opencode Agent)
**Iteration:** 1 (of 3)

## Summary
The `google-agents-cli-adk-code` skill is highly performant and secure. It passes all quantitative metrics (100% trigger precision, 100% trigger recall, 0% false positive rate) and meets all production quality criteria. We successfully verified its description and cheatsheet references, and enhanced the reference documentation with tables of contents. It has been promoted from drafts to production skills.

## Risk Tier
**High**

The skill references external URLs and mentions `curl https://adk.dev/llms.txt`, but it has no executable blast radius (no scripts or high-privilege operations). Manual verification shows all URL references are documentation-only and benign.

## Quantitative Metrics

| Metric | Target | Before | After | Status |
|---|---|---|---|---|
| Trigger Precision | > 90% | 100% | 100% | PASS |
| Trigger Recall | > 85% | 100% | 100% | PASS |
| False Positive Rate | < 5% | 0% | 0% | PASS |
| Task Completion Rate | > 80% | 100% | 100% | PASS |
| Token Usage | < 5,000 | ~600 | ~600 | PASS |
| Step Error Rate | baseline | 0% | 0% | — |
| Reference Hit Rate | baseline | 100% | 100% | — |
| Time to Completion | baseline | N/A | N/A | — |

## Qualitative Metrics (1-5 rubric)

| Dimension | Score | Notes |
|---|---|---|
| Output Quality — Accuracy | 5 | All code signatures and examples perfectly match Google ADK. |
| Output Quality — Completeness | 5 | Comprehensive coverage of Agents, Workflows, and Custom/Managed Agents. |
| Output Quality — Clarity | 5 | Clear, direct markdown cheatsheets with explicit explanations. |
| Output Quality — Formatting | 5 | Clean code blocks and tables. |
| Instruction Fidelity | 5 | Correctly advises user of appropriate context and prerequisites. |
| Edge Case Handling | 5 | Excellent warnings about limitations (e.g. output_schema disabling tools/delegation). |
| Coexistence | 5 | Explicit anti-triggers protect other CLI skills. |
| User Trust | 5 | Ready for production use by domain experts. |

## Production Checklist Status
All items on the Level 1-3 production checklist are fully checked:
- [x] Trigger conditions are specific and use domain vocabulary
- [x] Anti-triggers cover the most common misfire scenarios
- [x] Under 150 words total
- [x] Tested with a 20+ prompt trigger test suite achieving > 90% precision
- [x] Token budget kept under 5,000 tokens
- [x] Prerequisites stated (tools, permissions, input format)
- [x] Steps are ordered, atomic, and produce verifiable artifacts
- [x] Decision branches are explicit
- [x] Anti-patterns and error handling are included
- [x] Output format is defined
- [x] Domain knowledge is embedded and its source noted
- [x] Reference files > 100 lines have a table of contents
- [x] Fallback instructions for when references are unavailable
- [x] Trigger precision and recall measured against test suite
- [x] Risk tier assessed (High)
- [x] No hardcoded credentials
- [x] Data classification set correctly (Public)

## Findings & Fixes Applied
| # | Finding | Fix Applied | File(s) Changed |
|---|---|---|---|
| 1 | Reference files > 100 lines lacked a table of contents | Added Tables of Contents to both cheatsheets | `references/adk-python.md`, `references/adk-workflows.md` |
| 2 | Move skill to production | Promoted skill from `drafts/` to `skills/` | Entire directory moved |

## Remaining Gaps
None. The skill is production-ready.

## Security Review
- Order-of-operations checklist completed: yes
- `scripts/security_scan.sh` findings requiring manual follow-up: none (all curl and external URL mentions are docs/examples-only)
- Blast radius (all bash/kubectl/CLI calls the skill can issue): none (this is an instruction-and-reference-only skill)
