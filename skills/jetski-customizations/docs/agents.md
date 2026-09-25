# Custom Agents

Custom agents allow you to define tailored execution contexts for the Jetski
Agent. You can configure them with custom system prompts, specific tool sets,
and even arbitrary executable logic.

A Custom Agent can be used in two ways:

*   **Custom Main Agent**: Replaces the default Jetski agent for the workspace
    session.
*   **Custom Subagent**: Spawned from another agent using the `invoke_subagent`
    tool to delegate specialized tasks (e.g., code review, linting, deep
    research).

## Implementation Styles

There are three ways to define a custom agent:

1.  **Markdown Agent (`agent.md` — Preferred)**: A single Markdown file defining
    the agent's YAML frontmatter and system prompt body. Automatically includes
    standard default prompt sections (`user_information`, `mcp_servers`,
    `skills`, `messaging`, `artifacts`, `guidelines`, `communication_style`,
    plus `subagents`).
2.  **Declarative Agent (`agent.json` + `config.yaml` with `agent_config:`)**: A
    directory containing an `agent.json` manifest pointing to a `config.yaml`
    file using the canonical `agent_config` schema. Required when an agent needs
    internal Google3 prompt sections (`google_identity`,
    `google_user_information`, `google3_infrastructure`, `user_rules`,
    `conversation_transcript`), custom prompt section selection or interleaving,
    or `cascade_config` runtime overrides.
3.  **Interactive Agent (Executable)**: A directory containing an `agent.json`
    manifest pointing to an executable binary or script that handles the
    interaction loop over stdin/stdout.

--------------------------------------------------------------------------------

## 1. Markdown Agents

Markdown agents are the standard, recommended way to define a custom agent. They
can be defined either as a single file `agents/<agent_name>.md` or inside a
directory as `agents/<agent_name>/agent.md` (when the agent bundles sibling
files such as agent-private skills).

### Format Example

```markdown
---
name: refactoring-expert
description: "Expert at refactoring code for readability and performance. Invoke this agent when the user asks to clean up or optimize code."
tools:
  - view_file
  - replace_file_content
  - run_command
mainAgent: true
subagent: true
commandExecutionPolicy: auto
---

# Refactoring Expert Persona

You are an expert software engineer specializing in code refactoring. Your goal is to make code cleaner, more maintainable, and more efficient.

# Guidelines

*   Prioritize readability over clever tricks.
*   Write comprehensive unit tests for any refactored code.
*   Explain your changes clearly.
```

### Frontmatter Fields

*   **`name`** (string, required): Unique name for the agent.
*   **`description`** (string, required): Description of the agent's role and
    when to use (or not use) it. Both `name` and `description` must be
    non-empty or the agent is skipped.
*   **`tools`** (array of strings, optional): Allowlist of tools to enable (e.g.
    `view_file`, `replace_file_content`, `write_to_file`, `run_command`,
    `code_search`). If omitted, inherits the default non-mutating tool set
    (`shared.DefaultTools`). Setting `tools: []` disables all tools.
*   **`excludeDefaultComponents`** (bool, optional, default: `false`): If
    `true`, disables all default prompt sections and default tools. Whichever
    tools are desired can be added back explicitly in `tools`. Lifecycle hooks
    remain active.
*   **`mainAgent`** (bool, optional, default: `true`): If `true`, this agent can
    be selected as the main agent in the UI.
*   **`subagent`** (bool, optional, default: `true`): If `true`, this agent can
    be invoked as a subagent via `invoke_subagent`.
*   **`model`** (string, optional): Model tier used **only when run as a
    subagent**: `"inherit"`, `"flash_lite"`, `"flash"`, or `"pro"`.
*   **`commandExecutionPolicy`** (string, optional): Controls shell command
    auto-execution. Options: `"off"`, `"auto"`, `"eager"`, `"sandbox"`.
*   **`inheritCustomizations`** (bool, optional, default: `true`): If `true`,
    inherits ambient skills, plugins, rules, subagents, and hooks from user and
    workspace scopes. Does not affect MCP inheritance.
*   **`inheritMcp`** (bool, optional): If `true`, inherits the user's MCP
    servers (defaults to `true` when `mcpServers` is omitted, or `false` when
    `mcpServers` is specified).
*   **`mcpServers`** (array of objects, optional): Inline MCP server definitions
    scoped to this agent.
*   **`skills`**, **`plugins`**, **`rules`**, **`agents`**, **`hooks`** (array
    of strings, optional): Explicit customization paths (`//google3/...` for
    workspace-relative paths, `/...` for absolute paths, or `skills/...` for
    agent-relative paths).
*   **`hidden`** (bool, optional, default: `false`): Hide from agent pickers.
*   **`disabled`** (bool, optional, default: `false`): Skip loading the agent.

The body of the Markdown file is split into prompt sections **only** by H1
(`# `) headers (`splitMarkdownSections`). Subheadings (`## `, `### `) remain
inside the enclosing H1 section; if a Markdown body uses only `## ` headers
without any `# ` header, the entire body collapses into a single section titled
`"System Prompt"`. By default, `defaultPromptSections` (`user_information`,
`mcp_servers`, `skills`, `messaging`, `artifacts`, `guidelines`,
`communication_style`, plus `subagents` when `invoke_subagent` is enabled) are
automatically appended unless `excludeDefaultComponents: true` is set.

--------------------------------------------------------------------------------

## 2. Declarative Agents (YAML)

Declarative agents use a directory structure:

```text
agents/<agent_name>/
├── agent.json        # Required: Manifest
└── config.yaml       # Required: Configuration
```

### Manifest (`agent.json`)

The `agent.json` file declares the agent's identity and points to the config
file.

```json
{
  "name": "structured-planner",
  "description": "An agent that creates detailed, structured plans for complex tasks.",
  "configPath": {
    "relativePathToConfig": "config.yaml"
  }
}
```

*   **`name`** (string, required): Unique name.
*   **`description`** (string, required): Description for subagent selection.
*   **`configPath.relativePathToConfig`** (string, required): Path to the YAML
    config relative to `agent.json`.

### Configuration (`config.yaml`)

In `config.yaml`, always use the canonical top-level **`agent_config`** field
(`CustomAgentSpec.agent_config`). Unlike Markdown agents, declarative YAML
configs include **zero** implicit prompt sections—every built-in and custom
section must be listed explicitly in `agent_config.mixin_config.prompt_sections`.

```yaml
agent_config:
  mixin_config:
    prompt_sections:
      - builtin_name: google_identity
      - builtin_name: google_user_information
      - builtin_name: google3_infrastructure
      - custom:
          title: "Refactoring Instructions"
          content: |
            You are a refactoring assistant. Focus on improving code quality...
      - builtin_name: user_rules
      - builtin_name: conversation_transcript
      - builtin_name: mcp_servers
      - builtin_name: skills
      - builtin_name: subagents
      - builtin_name: messaging
      - builtin_name: artifacts
      - builtin_name: guidelines
      - builtin_name: communication_style
    tools:
      - name: code_search
        builtin: true
      - name: view_file
        builtin: true
      - name: grep_search
        builtin: true
      - name: run_command
        builtin: true
      - name: replace_file_content
        builtin: true
      - name: write_to_file
        builtin: true
      - name: send_message
        builtin: true
      - name: schedule
        builtin: true
    post_invocation_hooks:
      - name: terminal_step_check
        builtin: true
      - name: max_generator_invocations
        builtin: true
      - name: empty_output_continuation_check
        builtin: true
      - name: force_invocation
        builtin: true
  customization_discovery:
    skills:
      inherit_user: true
      skills_paths:
        - workspace_relative: "google3/learning/gemini/agents/skills/unit_test"
        - agent_relative: "skills"
    rules:
      inherit_user: true
    agents:
      inherit_user: true
  cascade_config:
    planner_config:
      tool_config:
        run_command:
          auto_command_config:
            auto_execution_policy: CASCADE_COMMANDS_AUTO_EXECUTION_AUTO
```

#### Key `agent_config` Fields

*   **`mixin_config`** (object):
    *   `prompt_sections` (array): Ordered list of `PromptSectionItem` entries,
        interleaving `builtin_name` (e.g. `google_identity`,
        `google_user_information`, `google3_infrastructure`, `user_information`,
        `user_rules`, `skills`, `subagents`, `messaging`, `artifacts`,
        `guidelines`, `communication_style`) and `custom` (`title` + `content`).
        Unknown `builtin_name` values fail fast at startup.
    *   `tools` (array): List of `NamedItem` entries (`name` + `builtin: true`
        or `provider_name: <mcp_server>`).
    *   `post_invocation_hooks` (array): Loop-control hooks required for main
        agents (`terminal_step_check`, `max_generator_invocations`,
        `empty_output_continuation_check`, `force_invocation`).
*   **`customization_discovery`** (object): Configures `skills`, `rules`,
    `plugins`, `agents`, `hooks`, and `mcp` discovery (`inherit_user` and
    `workspace_relative`, `agent_relative`, or `absolute` paths).
*   **`cascade_config`** (object): Runtime overrides, including command
    auto-execution policy (`CASCADE_COMMANDS_AUTO_EXECUTION_OFF`,
    `CASCADE_COMMANDS_AUTO_EXECUTION_AUTO`,
    `CASCADE_COMMANDS_AUTO_EXECUTION_EAGER`,
    `CASCADE_COMMANDS_AUTO_EXECUTION_PROCEED_IN_SANDBOX`).

> [!WARNING]
> **Avoid legacy `coding_agent:`, `custom_agent:`, and top-level
> `CustomAgentSpec` fields.**
>
> *   When `agent_config` is set, `ResolveCustomAgentSpec` returns early and
>     ignores top-level fields such as `command_execution_policy`,
>     `prompt_section_customization`, and `customization_config`.
> *   Do **not** configure agents with `coding_agent:` and
>     `prompt_section_customization:`: the CLI synthesizes a default built-in
>     agent spec that causes `convertinputs.go` to discard the static config,
>     and Core Direct conversion does not map `prompt_section_customization`
>     into declarative prompt sections (b/563398383).

--------------------------------------------------------------------------------

## 3. Interactive Agents (Executable)

Interactive agents run as persistent external processes. They are useful when
you need complete control over the agent's reasoning loop or need to integrate
with external systems.

### Manifest (`agent.json`)

```json
{
  "name": "custom-loop-agent",
  "description": "Runs a custom execution loop for specialized tasks.",
  "command_spec": {
    "command": "blaze",
    "args": ["run", "//path/to/your/agent:binary"]
  }
}
```

*   **`command_spec.command`** (string, required): The executable to run.
*   **`command_spec.args`** (array of strings, optional): Arguments to pass to
    the executable.

### Execution Loop and SDK

Interactive agents receive `init` metadata and turn `input` requests line-by-line over stdin from the Jetski Language Server, and communicate back via Connect RPC over HTTP (or gRPC) to deliver messages (`SendAgentMessage`) and signal turn completion (`SignalExecutableIdle`).

To simplify development, use the **Antigravity Python SDK**
(`//third_party/jetski/sdk/py/interactive.py`), which provides helpers like
`run_persistent` and decorators for registering custom tools and lifecycle
hooks.

