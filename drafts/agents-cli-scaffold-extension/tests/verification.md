# Creator verification

Verified 2026-09-14 on Linux, Python 3.12.3 and Node 20.19.3 (npm 11.6.1).
This is implementation verification, not a trigger evaluation or model-quality
benchmark. The evaluator can use these commands to reproduce it.

## Checks and results

- `python3 -B -m unittest discover -s tests -p 'test_*.py' -v` from the
  skill directory: **5 tests passed**. Covers write-free dry-run, customized
  names/ports/model with exact file manifest, output paths containing spaces,
  preserving an existing directory, rejecting dangling symlinks, and invalid
  names/model/ports/missing-parent rejection (seven invalid-input subcases).
- Generated `/tmp/opencode/polyglot-check` with the bundled script, first with
  `--dry-run` and then without it. Twelve files generated.
- In that generated workspace: `npm install --ignore-scripts --no-audit --no-fund`
  and `npm run build`: **passed**. Installed pinned Hono/adapter/TypeScript.
- Created a dedicated `.venv` and installed the generated `requirements.txt`:
  **passed**, google-adk 1.18.0 installed.
- `python3 -B tests/verify_runtime.py /tmp/opencode/polyglot-check`:
  **passed** against the actual installed ADK API server and built Hono server.
  Two-stage demo returned exact input-derived text, separate requests got
  different sessions and correct text, four malformed request shapes returned
  400, and stopping ADK caused Hono to return 502. Child processes were stopped
  in `finally`. The verifier chooses ephemeral ports and needs no credentials.
- YAML frontmatter parsed, description **560 characters / 75 words**, name
  matches folder; body is under the skill token budget.
- All bundled Python parsed with `ast.parse`; no bytecode artifacts required.
- Draft 2020-12 checked both the workspace descriptor schema and generated
  message schema using `jsonschema`. Generated workspace and valid message
  instances passed; descriptor with port 0 was rejected.

## Scope of evidence

The generator is stdlib-only. Running the generated application requires its
declared npm and Python dependencies. Direct versions are pinned; the test's
resolved transitive dependencies are not a committed lockfile. No real LLM
call was performed. Demo mode verifies the real ADK API and state/event
machinery with deterministic agents. The 60-second timeout branch and hosted
deployment were not exercised. Dependencies and generated runtime files live
in a temporary workspace, not in this skill bundle.
