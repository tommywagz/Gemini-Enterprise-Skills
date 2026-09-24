# Black-Box Test Design

## Sources

- ISTQB CTFL v4.0.1: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
- ISO/IEC/IEEE 29119 series overview: https://standards.ieee.org/wp-content/uploads/import/documents/tocs/ISO_IEC_IEEE_29119.pdf

## Boundary-Oriented Oracles

Use behavior visible to a caller: responses, exit codes, emitted files,
durable state, readiness, authorization result, or post-shutdown behavior.
An implementation detail can guide investigation but must not be the expected
outcome. Associate each test with a requirement or documented public contract.

## Equivalence Partitions and Boundaries

For every input, define valid and invalid classes before choosing cases. Select
one representative per class unless another dimension changes the expected
result. For a documented numeric interval `[minimum, maximum]`, test
`minimum - 1`, `minimum`, a typical valid value, `maximum`, and `maximum + 1`.
For strings, consider omitted, empty, valid minimum length, typical valid,
maximum, one character over maximum, malformed encoding, and wrong type when
the boundary accepts structured data.

## Decisions and States

For multi-rule behavior, write a decision table with each condition and
expected action. Explicitly label impossible combinations and why they are
impossible. Do not collapse a permission rule into a malformed-input case.

Model each lifecycle state, permitted event, expected new state, and rejected
event. Cover normal transitions, forbidden transitions, recovery transition,
and terminal state. Example: `stopped --start--> ready --stop--> stopped`;
`stopped --request--> rejected`; `degraded --dependency-restored--> ready`.

## Lifecycle Matrix Example

| Matrix ID | Boundary | Scenario | Observable oracle | Classification if unavailable |
|---|---|---|---|---|
| L-DEPLOY | deployment | fresh start reaches readiness | documented health signal | skipped if runtime missing |
| L-USE | normal use | valid representative request | response and durable effect | fail |
| L-FAIL | recovery | dependency loss then restore | documented error then recovery | inconclusive if fixture failed |
| L-STOP | shutdown | graceful stop and repeat start | exit behavior and state | fail |

## Fixture Discipline

Use unique names, paths, ports, and identities per test. Prove readiness before
the product assertion. Cleanup must tolerate a partially-started target and be
safe to rerun. Preserve enough local evidence to diagnose a result without
leaking secrets into reports.
