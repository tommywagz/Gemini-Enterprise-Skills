# JSON Configuration Files

JSON configuration files allow you to explicitly register and manage
customizations that are stored outside the default discovery locations (such as
project-specific folders or shared team directories in Piper).

Each customization type has its own configuration file, placed in your
customization root directory (e.g., `_agents/` in google3, or
`~/.gemini/config/` globally, or within a plugin):

*   **Skills**: `skills.json`
*   **Rules**: `rules.json`
*   **Agents**: `agents.json`
*   **Plugins**: `plugins.json`

## Configuration Schema

All configuration files share the same schema, allowing you to declare path
entries and inherit from other configurations.

```json
{
  "exclude": ["global-deprecated-skill"],
  "inherits": [
    {
      "path": "/google/src/head/depot/google3/experimental/team/shared_skills/skills.json",
      "include_only": ["linter-skill"],
      "exclude": ["deprecated-skill"]
    }
  ],
  "entries": [
    {
      "path": "google3/java/com/google/myteam/skills",
      "exclude": ["experimental-.*"]
    },
    {
      "path": "~/personal-skills"
    }
  ]
}
```

> [!NOTE] `rules.json` is the recommended way to share rule content across
> directories or teams. Rules it registers keep their frontmatter and trigger
> conditions, and its `entries` directories are scanned one level deep. See the
> [Rules Guide](./rules.md).

### Top-Level Fields

*   **`exclude`** (array of strings, optional): A global exclusion list of
    directory names or `/`-delimited path suffixes. Matching customizations are
    excluded across all `entries`, `inherits`, and shared or default discovery
    locations, even when `exclude` is the only field in the configuration file.
*   **`entries`** (array of objects, optional): A list of path entries to scan
    for customizations of this type. Each entry directory is scanned **one level
    deep**.
*   **`inherits`** (array of objects, optional): A list of other configuration
    files to inherit from. The entries from inherited files are merged with your
    local entries. Inherited files are processed in the order they are listed.

### Path Entry Fields

Each object in the `entries` or `inherits` array supports the following fields:

| Field          | Type             | Required | Description                   |
| :------------- | :--------------- | :------- | :---------------------------- |
| `path`         | string           | Yes      | The path to the customization |
:                :                  :          : directory (for `entries`) or  :
:                :                  :          : another JSON config file (for :
:                :                  :          : `inherits`).                  :
| `include_only` | array of strings | No       | Patterns naming items         |
:                :                  :          : relative to `path`. If        :
:                :                  :          : specified, only matching      :
:                :                  :          : customizations will be        :
:                :                  :          : loaded.                       :
| `exclude`      | array of strings | No       | Patterns. Customizations      |
:                :                  :          : whose directory names match   :
:                :                  :          : any of these patterns will be :
:                :                  :          : skipped.                      :

### Scan Depth and Migrating Nested Directories

An entry directory is scanned **one level deep**, matching standard
`_agents/skills/` discovery: `{ "path": "google3/myteam/skills" }` discovers
`.../skills/my-skill/SKILL.md`, but does not recursively scan nested category
folders like `.../skills/category/my-skill/SKILL.md`.

If an existing directory uses nested category folders, migrate based on your
role:

*   **For Customization Directory Owners (Shared Team Repositories)**:
    *   **Flatten or Symlink at Top Level (Recommended)**: Place each
        customization at `<dir>/<name>/SKILL.md` or add top-level symlinks
        (`<dir>/<name> -> <category>/<name>`). Directory symlinks at depth 1 are
        followed automatically, fixing discovery for all subscribers without
        changing their personal configs.
    *   **Publish a Shared Config File**: Provide a shared `skills.json` in your
        repo listing each category folder in `entries` so users can subscribe
        via `inherits`.
*   **For Individual Users (Personal Configs)**:
    *   **Point `entries` to Category Subdirectories**: List each category
        folder as its own entry (`{ "path": "google3/myteam/skills/category-a"
        }`).
    *   **Name Subpaths in `include_only`**: Keep `"path":
        "google3/myteam/skills"` and list relative subpaths in `include_only`
        (`"include_only": ["category-a/my-skill"]`).

## Explicitly Configured Paths

Config files are also honored on explicitly configured customization paths (e.g.
`skills_paths` in an agent's customization discovery config) when the configured
path points directly at a config file (e.g. `path/to/skills.json`). A configured
directory keeps its regular one-level scan; a manifest inside it is not
expanded. Directories referenced from manifest `entries` follow the standard
entry scan rules described above, and top-level `exclude` patterns apply across
all explicitly configured paths, not just the one that declared them. They never
filter customizations inherited from the user's environment.

## Path Resolution Rules

Jetski resolves the `path` field based on the following rules:

1.  **Absolute Paths**: Paths starting with `/` are treated as absolute local
    filesystem paths.
2.  **Home-Relative Paths**: Paths starting with `~/` are resolved relative to
    the user's home directory.
3.  **Workspace-Relative Paths**:
    *   In **Google3 (CitC)**, paths starting with `google3/` or `configs/` are
        resolved relative to the root of your active CitC workspace (e.g.,
        `google3/path/to/dir` maps to
        `/google/src/cloud/username/workspace/google3/path/to/dir`), falling
        back to `/google/src/files/head/depot/` if not present locally.
    *   In **Non-Google3** environments (such as Android `repo` / Git-on-Borg or
        Cog checkouts), paths are resolved relative to the customization base
        directory or repository root first, and **automatically fall back to
        `/google/src/files/head/depot/`** if not found in the workspace. This
        allows non-Google3 configs to reference relative `"google3/..."` and
        `"configs/..."` depot paths directly.

### Pro-Tip: Stable Team Sharing in Google3

When sharing configurations across a team, you want them to work regardless of
whether a team member is in an active workspace or using a global surface.

*   **The Shared Config (Checked into Piper)**: Store your team's skills/agents
    in a central directory (e.g., `google3/experimental/team/shared/`) and
    create a `skills.json` there pointing to them.
*   **The User Subscription (Local Global Config)**: Teammates should reference
    the shared config in their global `~/.gemini/config/skills.json` using a
    **read-only depot snapshot path**:

    ```json
    {
      "inherits": [
        { "path": "/google/src/head/depot/google3/experimental/team/shared/skills.json" }
      ]
    }
    ```

    Using `/google/src/head/depot/google3/...` ensures the path is always
    resolvable by the Jetski backend, even if the user has no workspace open.
