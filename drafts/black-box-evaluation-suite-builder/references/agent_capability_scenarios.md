# Outcome-Based Agent Scenarios

## Sources

- SWE-bench: https://arxiv.org/abs/2310.06770
- GAIA: https://arxiv.org/abs/2311.12983
- AgentBench: https://arxiv.org/abs/2308.03688
- WebArena: https://arxiv.org/abs/2307.13854
- ToolBench/ToolLLM: https://arxiv.org/abs/2307.16789
- MINT: https://arxiv.org/abs/2309.10691

## Scenario Families

| Inspiration | Local scenario pattern | Observable pass condition |
|---|---|---|
| SWE-bench | Give a bounded issue and fixture repository | Tests pass and requested external behavior changes |
| GAIA | Require multi-step reasoning plus a fixture file/image/tool | Correct final answer or artifact from approved inputs |
| AgentBench | Limit turns, tools, and allowed actions | Valid actions and completed constrained objective |
| WebArena | Use a local UI or sandbox API with a stateful task | Required final UI or service state exists |
| ToolBench | Provide discoverable fake API documentation | Valid endpoint/arguments and correct resulting state |
| MINT | Inject one deterministic tool error or user correction | Agent recovers and communicates the correction clearly |

## Construction Rules

Define the initial state, user objective, allowed tools, prohibited effects,
turn/timeout budget, injected fault, expected final state, and scoring evidence.
Use local fixtures or approved sandbox services. Permit multiple action paths
when they reach the same safe final state. Capture actions for validity review,

Score four dimensions separately: completed outcome, valid tool actions,
recovery after the controlled fault, and user-facing clarity. A tool action can
be invalid even if the final state happens to look correct. An unavailable
sandbox is a skipped scenario; an ambiguous final state is inconclusive.
