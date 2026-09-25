# Workspace Rules

Rules are guidelines and constraints that the agent must follow when operating
within specific directories. They are useful for enforcing coding styles, API
usage restrictions, or safety protocols.

## Rule Locations

The system automatically discovers and applies rules from the following
locations:

*   **Workspace Rules**: Placed in `_agents/rules/` within your project.
*   **Global Rules**: Placed in `~/.gemini/config/rules/` (applies to all
    workspaces).
*   **Directory-Based Rules (`GEMINI.md` / `AGENTS.md`)**: Placed directly in
    any directory (or inside `_agents/AGENTS.md`). The system walks up from the
    current working directory to the repository root and loads these files. They
    apply to the directory they reside in and all its subdirectories.
*   **Registered Rules (`_agents/rules.json`)**: A JSON config that registers
    rule files stored *elsewhere*, so several projects can share one canonical
    copy. Like the locations above, it is discovered by walking up from the
    current directory to the repository root. See
    [JSON Configurations](./json_configs.md).

## Rule Format and Frontmatter

Rules are written in Markdown. Rules placed in `rules/` directories can
optionally include a YAML frontmatter block to configure their activation
behavior. Standalone `GEMINI.md` / `AGENTS.md` files do not support frontmatter
and are always active for their directory scope.

```markdown
---
trigger: model_decision
description: "Use these rules when modifying C++ files to ensure style compliance."
---

# C++ Style Guidelines

*   Use `std::unique_ptr` for exclusive ownership.
*   Never use raw `new` or `delete`; prefer `absl::make_unique` or `std::make_unique`.
*   Follow the Google C++ Style Guide.
```

### Frontmatter Fields

*   **`trigger`** (string, required): Defines how the rule is activated.
    Supported modes:
    *   **`always_on`**: The rule is always injected into the system prompt for
        every turn. Use sparingly to avoid token bloat.
    *   **`model_decision`**: The rule is listed as available, and the model
        dynamically decides whether to read the full content based on the
        current task. **Requires the `description` field.**
    *   **`glob`**: The rule is automatically activated if any file currently
        open or being edited matches the patterns specified in the `globs`
        field. **Requires the `globs` field.** Expected to be deprecated — do
        not recommend it for new rules; scope the rule by placing it in the
        relevant directory instead.
    *   **`manual`**: The rule is only activated if the user explicitly
        @-mentions it in the chat. Expected to be deprecated — use a plain
        Markdown file in `docs/` and reference it on demand instead.
*   **`description`** (string, required for `model_decision`): Explains what the
    rule covers, helping the model decide when to load it.
*   **`globs`** (string, required for `glob`): A comma-separated list of glob
    patterns (e.g., `*.cc,*.h`). You can also use the singular key `glob`.

## Sharing Rules Across Projects (`rules.json`)

`_agents/rules/` and `AGENTS.md` both require rule content to live in the
directory it applies to. `_agents/rules.json` lifts that restriction: it
registers rules stored elsewhere, letting many projects share one canonical set
while still adding their own.

```json
{
  "inherits": [
    { "path": "google3/experimental/myorg/shared/_agents/rules.json" }
  ],
  "entries": [
    { "path": "project_rules" }
  ]
}
```

*   `entries` directories are scanned **one level deep**, matching standard
    `_agents/rules/` scanning. To reach a nested rule file, name its relative
    subpath in `include_only` (e.g., `"include_only": ["nested/style.md"]`), or
    point `entries` directly at each rule subdirectory. See
    [JSON Configurations](./json_configs.md) for migration options.
*   Registered rules are parsed as ordinary rule files, so **frontmatter and
    trigger conditions are preserved**. This is the key difference from
    `@[label](path)` includes, which splice raw text and drop frontmatter.
*   Relative paths resolve against the directory containing the dot-dir;
    `google3/...` paths resolve against the workspace root; absolute paths
    (including `/google/src/head/depot/google3/...`) are used as-is.

## Rule Merging and Deduplication

*   Rules are automatically deduplicated. Even if a rule is discovered via
    multiple paths (e.g., inherited from parent directories), it is only applied
    once per conversation.
*   If a rule is defined in a plugin, it is loaded when the plugin is enabled.

## Size Limits and Context Budget

*   **Per-File Limit (`24 KB` / `24,000` bytes)**: Each rule file is capped at
    24,000 bytes (evaluated after expanding `@[label](path)` includes) and
    truncated on line boundaries if it exceeds the limit. Use a skill or
    `trigger: model_decision` for larger reference documents.
*   **Aggregate Rules Budget (`20,000` tokens)**: Always-on and global rules
    share a dedicated 20,000-token rules budget (`defaultRulesBudget`),
    separate from the customization budget for skills, workflows, subagents,
    and MCP tools. When total rule usage exceeds 20,000 tokens, the largest
    rules are selected first and demoted from full inline text to
    `- <path>: <description>` pointers (or `- <path>` when no frontmatter
    `description` is defined, such as for `AGENTS.md`) at the end of
    `<user_rules>` so the agent can read them on demand via `view_file`.
