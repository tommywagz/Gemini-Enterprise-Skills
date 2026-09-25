# Plugins

Plugins are namespaced, shareable bundles that package **Skills**, **Agents**,
**Rules**, **Hooks**, and **MCP Server Configurations** into a single deployable
unit. They are the recommended way to distribute complex, feature-rich
customizations to your team.

--------------------------------------------------------------------------------

## Directory Structure

A plugin must be contained within a subdirectory of a `plugins/` folder in a
customization root (e.g., `_agents/plugins/` in google3).

```text
plugins/<plugin_name>/
├── plugin.json       # Required: Manifest file
├── README.md         # Optional: Human-facing docs, shown in the Marketplace
├── mcp_config.json   # Optional: MCP servers exposed by the plugin
├── hooks.json        # Optional: Lifecycle hooks run by the plugin
├── rules.json        # Optional: Root-level rules configuration
├── skills.json       # Optional: Root-level skills configuration
├── rules/            # Optional: Rule directory
│   ├── AGENTS.md     # Recommended consolidated rules file
│   └── <rule_name>.md # Individual rule markdown files
├── skills/           # Optional: Skill directory
│   └── <skill_name>/ # Individual skill directories
│       └── SKILL.md
├── agents/           # Optional: Custom agents exposed by the plugin
│   └── <agent_name>.md # Markdown agent (or legacy <agent_name>/agent.json)
└── sidecars/         # Optional: Background processes, including UI panes
    └── <sidecar_name>/
        └── sidecar.json
```

--------------------------------------------------------------------------------

## Manifest (`plugin.json`)

The `plugin.json` file serves as the marker declaring the directory as a plugin.

```json
{
  "name": "team-developer-kit",
  "description": "What the plugin does and who it is for.",
  "logo": "assets/logo.svg",
  "suggestedPrompts": [
    "Check service health and error budget burn over the last 24h",
    "Search team design docs for tenant isolation architecture",
    "Scaffold a new RPC handler with hermetic unit tests"
  ]
}
```

*   **`name`** (string, optional): The display name of the plugin. If omitted,
    it defaults to the directory name.
*   **`description`** (string, optional): One or two sentences. This is what
    users read in the Marketplace, and what its search matches.
*   **`logo`** (string, optional): A path relative to `plugin.json`, or an
    `https` URL on a Google-owned domain.
*   **`suggestedPrompts`** (array of strings, optional): Up to 3 starter prompts
    for card and detail views. Exactly 3 prompts are recommended for UI card
    layouts. Empty strings are skipped and additional prompts beyond 3 are
    ignored.

*   **`displayName`** (string, optional): Human-readable presentation title
    shown in UI headers, cards, and slash command menus.
*   **`version`** (string, optional): Semantic version string.

Unknown top-level fields are silently discarded. `author` is **not** read; do not add it.

### Name versus directory

Two identifiers, not interchangeable:

*   The **manifest `name`** is the display label and the global deduplication
    key: two plugins claiming the same `name` collide and only the first
    discovered is loaded. It namespaces the plugin's sidecars, but **not** its
    MCP servers, which keep the name given in `mcp_config.json`.
*   The **install directory name** is the install identity. Install, uninstall,
    enable, and disable all key on it.

--------------------------------------------------------------------------------

## How Plugins Work

When a plugin is discovered and enabled:

1.  **Automatic Ingestion**: All skills, agents, rules, hooks, and MCP servers
    defined within the plugin's directory structure are automatically loaded.
2.  **Collision handling**: Skills and other customizations are deduplicated by
    name, with the first discovered winning. Only sidecars are namespaced by the
    plugin name; MCP servers and their tools are not.
3.  **Lifecycle Scoping**:
    *   **Hooks** defined in `plugins/<name>/hooks.json` are registered and run
        during the agent's lifecycle.
    *   **MCP Servers** defined in `plugins/<name>/mcp_config.json` are
        launched, and their tools are made available.
    *   **Rules** in `plugins/<name>/rules/` are merged into the active rule
        set. Placing a consolidated **`AGENTS.md`** (or `GEMINI.md`) file under
        `rules/` (e.g., `rules/AGENTS.md`) is recommended over separate rule
        files.

## Registering Plugins

Plugins can be discovered automatically if placed in standard customization
roots, or they can be explicitly registered using `plugins.json`.

*   See the [JSON Configurations Guide](./json_configs.md) for details on how to
    use `plugins.json` to enable specific plugins or inherit them from shared
    team paths.

## Turning Plugins On and Off

Most discovered plugins are **enabled by default**; a plugin can ship switched
off by declaring `"disabled": true` in its `plugin.json`, and some built-in ones
do. Whether a plugin is active is recorded in the user's `config.json`, under a
`plugins` map keyed by the plugin's **directory** name:

```json
{
  "plugins": {
    "my-plugin": { "enabled": false }
  }
}
```

The setting can be changed from the plugin section of the settings UI, or from
the CLI's `plugin enable` / `plugin disable` subcommands, both of which write
this entry.

`config.json` wins wherever it has an entry, so a user's choice always beats
what the plugin declares. A plugin with no entry falls back to its `plugin.json`
declaration, which is how a plugin that ships disabled stays off until the user
turns it on. Jetski never records a preference inside the plugin itself, so the
choice survives reinstalling or updating the plugin.

A disabled plugin still appears in the plugin list so it can be turned back on,
but none of its bundled customizations are loaded.
