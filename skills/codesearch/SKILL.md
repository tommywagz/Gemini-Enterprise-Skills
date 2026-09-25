---
name: codesearch
description: >-
  How to search google3 or Cog repositories with Google Code Search. Always
  prefer it over alternatives like the `cs` CLI, find, grep, or manually
  traversing files.
---

# `codesearch-for-agents`

Indexed, workspace-scoped search over google3 and Cog repositories.

## Usage

```bash
codesearch-for-agents --query '<QUERY>' [flags]
```

Run from inside a CitC or Cog workspace — scoping is derived from the working
directory. The index covers submitted code plus **your own uncommitted edits in
the workspace you are running from**. Another workspace of yours, and anyone
else's unsubmitted CL, is invisible to it.

| Flag | Default | Meaning |
|---|---|---|
| `--query STRING` | *required* | Query, including filters. Always single-quote it. |
| `--only_paths` | `false` | Paths only, no snippets. |
| `--allow_dirs` | `false` | Include directories in results. |
| `--max_num_results INT` | `50` | Max files returned. |
| `--max_matches_per_file INT` | unlimited | Max matches shown per file. |

## Output

```
97 files found, showing 50:

third_party/jetski/cortex/core/tools/registry.go
    42: func NewRegistry(env *env.Env) *Registry {
   118:         registry.Register(name, tool)
        (+3 more matches)
```

Paths are relative to the workspace root, so they can be handed straight to
`view_text` or reused in an `f:` filter. Matches are sorted by line number.
`(+N more matches)` counts what `--max_matches_per_file` trimmed. Under
`--only_paths` only the path lines appear.

## When nothing matches

```
no files matched: <query>
```

This nearly always means the code is not in **this** workspace — not that the
query is malformed. Before re-querying:

- **Do not fall back to `grep`.** It reads the same files and cannot find what
  is not there.
- Confirm you are in the workspace that holds the code. Work you did in a
  different workspace is not searchable from this one.
- Drop filters one at a time; `f:` is the usual culprit. Rewording the search
  term rarely helps.
- Never re-run a query you have already run.

## Spending fewer queries

- **Open the top hit before refining.** Results are relevance-ordered and the
  answer is usually in the first file or two. Running another query instead of
  reading the first result is the most common way to waste a search.
- **Start exploratory queries with `--only_paths`.** The shape of the paths
  usually tells you where to look, at a fraction of the output.
- **Cap anything broad.** A bare term like `multicall` matches tens of thousands
  of files and still prints 50 of them in full. Add `f:` and
  `--max_num_results`.

## Query syntax

RE2 regex, case-insensitive, matched against content **and** path. A space means
AND; `OR` (uppercase) also works; group with ` ( ) ` (spaces required).
`"quoted"` is a literal. Results are ordered by relevance, so
`--max_num_results` keeps the best N, not the first N. Only Piper-managed source
is indexed, so build outputs (`blaze-bin/`, `blaze-out/`, ...) never match.

A leading `-` on a term excludes it (`-f:experimental`). A hyphen **inside** a
word is an ordinary character: `--query 'codesearch-for-agents'` searches for
that literal string and does not negate anything.

| Filter | Meaning |
|---|---|
| `f:` / `file:` | Path regex, matched against `//depot/...`. |
| `l:` / `lang:` | Language, e.g. `l:python`, `l:java\|proto`. |
| `c:` / `content:` | Contents only, excluding filenames. |
| `s:` / `symbol:`, `class:`, `func:` | Symbol, class, or function name. |
| `comment:`, `within:-comment`, `usage:` | Inside comments / outside them / outside comments and string literals. |
| `trait:dir`, `trait:citc` | Directories only; CitC-touched files only. Negate with `-`. |
| `a:` / `author:`, `blame:` | Modified by / last touched by a user. |
| `at_cl:`, `from:`, `to:`, `removed:yes` | Revision-visibility and deletion filters. |
| `case:auto`, `matcher:fuzzy`, `pcre:yes` | Case sensitivity, matcher engine, PCRE (`pcre:yes (?ms)a.*?b`). |
| `proximity:<depot_path>`, `snippet:<block\|comment>` | Boost files near a path; widen snippets to a whole block. |

```bash
codesearch-for-agents --query 'func:\bMyMethod\b l:cpp f:^//depot/google3/net/rpc'
codesearch-for-agents --query '( l:java OR l:py ) c:MyClass -f:experimental' --only_paths
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unexpected positional argument(s)` | The query was not quoted and the shell split it. |
| `...workspace is not yet indexed` | Wait; indexing lags submits by up to ~3 minutes. |
| `failed to resolve workspace for <dir>` | The working directory is not in a CitC/Cog workspace. |
| `RPC::UNREACHABLE: no connections available` | Transient; if it persists, run `gcert`. |
| No hits for a file you can see on disk | It is a build output, it is in another workspace, or the edit is newer than the index. |
