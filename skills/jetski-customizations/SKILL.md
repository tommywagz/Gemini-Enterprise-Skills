---
name: jetski-customizations
description: >-
  Comprehensive guide and reference for the Jetski Customization System.
  Use to explain how customizations work, their loading priority, discovery mechanisms,
  and to guide the creation of skills, rules, agents, plugins, hooks, and MCP servers.
---

# Jetski Customization System Guide

The Jetski Customization System allows you to tailor the agent's behavior, teach
it new workflows, enforce guidelines, and integrate it with external tools. By
customizing the agent, you can transition it from a general-purpose assistant to
an expert pair programmer specialized in your team's codebase and processes.

--------------------------------------------------------------------------------

## Customization Types: Quick Reference

Choose the right customization type based on your goal:

Type              | Config File/Folder                     | Scope                     | Best For                                                                                | Learn More
:---------------- | :------------------------------------- | :------------------------ | :-------------------------------------------------------------------------------------- | :---------
**Rules**         | `rules/*.md`, `GEMINI.md`, `AGENTS.md` | Contextual / Hierarchical | Enforcing coding styles, API restrictions, and local guidelines.                        | [Rules Guide](./docs/rules.md)
**Skills**        | `skills/<name>/SKILL.md`               | On-Demand (Progressive)   | Teaching the agent multi-step procedures, runbooks, and tool workflows.                 | [Skills Guide](./docs/skills.md)
**Custom Agents** | `agents/<name>/agent.json`, `*.md`     | Session / Subagent        | Defining specialized personas or subagents with custom tools and prompts.               | [Agents Guide](./docs/agents.md)
**Plugins**       | `plugins/<name>/plugin.json`           | Bundle                    | Packaging related skills, agents, rules, and MCP configs into a single unit.            | [Plugins Guide](./docs/plugins.md)
**Hooks**         | `hooks.json`                           | Lifecycle Event           | Running scripts/commands at specific agent lifecycle points (e.g., pre-tool execution). | [Hooks Guide](./docs/hooks.md)
**MCP Servers**   | `mcp_config.json`                      | Tool Integration          | Connecting the agent to external services and custom tool providers.                    | [MCP Guide](./docs/mcp_servers.md)

--------------------------------------------------------------------------------

## Customization Discovery and Locations

Jetski automatically discovers your own customizations by traversing specific
directories. The locations searched depend on your development environment.
Built-in customizations are not found this way: the agent config names the ones
it mounts.

### Google3 (Piper/CitC) Discovery Locations

In Google3, customizations are split into personal, project-scoped, and shared
locations:

1.  **Personal Piper Customizations** (Highest Priority):
    *   Path: `configs/users/%USERNAME%/_agents/`
    *   *Note: This directory is a root-level directory in Piper (sibling to
        `google3/`), NOT under `google3/configs/`.*
    *   Use this to store your personal skills, agents, and plugins that you
        want active across all your workspaces.
2.  **Directory & Project Rules** (Hierarchical):
    *   Paths: `GEMINI.md`, `AGENTS.md`, `_agents/rules/*.md` (with
        `trigger: always_on` only), `_agents/rules.json`
    *   As you open or edit files, Jetski walks up from the file's directory to
        the `google3/` root, surfacing `GEMINI.md` / `AGENTS.md` files and
        `_agents/rules/*.md` files configured with `trigger: always_on`.
3.  **Repository Shared Configuration**:
    *   Path: `google3/configs/jetski/_agents/`
    *   Shared customizations available to all Jetski users.
4.  **Global Configuration** (Machine-Local):
    *   Path: `~/.gemini/config/`
    *   Applies to all workspaces run from your machine.

> [!NOTE]
> **Hybrid Local + Depot HEAD discovery.** In Google3, customizations are
> resolved from a hybrid of your local CitC workspace and the read-only depot at
> HEAD (`/google/src/files/head/depot/...`). Files you have opened, edited, or
> added locally (tracked in your `.citc/manifest`) are served from your
> workspace and take precedence; any customization not touched locally falls
> back to its committed version at HEAD. This means shared, committed
> customizations are discovered even if they are not synced into your current
> client, while your uncommitted edits are still respected. Files you have
> locally deleted (manifest `TOMBSTONE` entries) are excluded entirely.

--------------------------------------------------------------------------------

## Loading Priority and Precedence

When multiple customizations are discovered, they are loaded and applied in a
specific order. If there are naming conflicts (e.g., two skills with the same
name), the higher-priority customization overrides the lower-priority one.

The priority order (from highest to lowest) is:

1.  **Workspace Personal**: `configs/users/%USERNAME%/_agents/`
2.  **Workspace Project**: Hierarchical discovery walking up from the CWD.
3.  **Repository Shared**: `google3/configs/jetski/_agents/`
4.  **Declared Configurations**: Customizations explicitly listed in
    `skills.json`, `agents.json`, or `plugins.json` (evaluated in the order of
    the files above).
5.  **Global Discovery**: `~/.gemini/config/`
6.  **Built-in Customizations**: Default skills and plugins bundled with Jetski,
    mounted by name rather than discovered.
7.  **Global Declared Configurations**: Explicitly listed in global JSON
    configs.

--------------------------------------------------------------------------------

## How Customizations are Applied

### Progressive Disclosure (Skills and Rules)

To prevent overwhelming the LLM's context window, Jetski uses **progressive
disclosure**:

*   **Skills** are not loaded into the context window by default. Only their
    names and descriptions are injected. The full content of a skill is only
    loaded if the model (or the user) explicitly decides to activate it.
*   **Rules** with `trigger: model_decision` behave similarly. Only `always_on`
    rules are loaded unconditionally.

### Deduplication

All customizations (especially rules) are deduplicated by their resolved file
paths. A rule file will never be injected more than once in a single
conversation turn, even if it matches multiple trigger conditions.

--------------------------------------------------------------------------------

## Advanced Management: JSON Configs

For customizations stored in non-standard locations, you can use `skills.json`,
`agents.json`, and `plugins.json` to explicitly register them and inherit from
shared configurations.

*   Learn how to configure these in the
    [JSON Configurations Guide](./docs/json_configs.md).
