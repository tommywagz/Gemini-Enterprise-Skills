# Production Checklist

Work through every box below when evaluating a skill for production
readiness. Unchecked items are the direct input to the "implement
improvements" step of the main workflow — each one maps to a concrete fix,
not a vague quality note.

## Description (Level 1)
- [ ] Trigger conditions are specific and use domain vocabulary
- [ ] Anti-triggers cover the most common misfire scenarios
- [ ] Under 150 words total
- [ ] Tested with a 20+ prompt trigger test suite achieving > 90% precision

## Body (Level 2)
- [ ] Token budget kept under 5,000 tokens
- [ ] Prerequisites stated (tools, permissions, input format)
- [ ] Steps are ordered, atomic, and produce verifiable artifacts
- [ ] Decision branches are explicit (if/else, not implied)
- [ ] Anti-patterns and error handling are included
- [ ] Output format is defined
- [ ] Domain knowledge is embedded and its source noted

## References (Level 3)
- [ ] Scripts tested independently before bundling
- [ ] Reference files > 100 lines have a table of contents
- [ ] Asset formats documented in the skill body
- [ ] Fallback instructions for when references are unavailable

## Validation
- [ ] Trigger precision and recall measured against test suite
- [ ] End-to-end integration tests passing
- [ ] Edge case and adversarial (red team) inputs tested
- [ ] A/B comparison with/without skill shows meaningful delta
- [ ] SME review completed

## Security
- [ ] Risk tier assessed (Low / Medium / High / Critical)
- [ ] Minimal tool set declared (no wildcards in production)
- [ ] Input validation instructions in body
- [ ] No hardcoded credentials anywhere in the skill directory
- [ ] Data classification set correctly
- [ ] Approval workflow configured for irreversible actions
