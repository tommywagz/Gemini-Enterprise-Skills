---
name: ui-plugin-development
description: >-
  Develop, package, configure, run, and debug UI plugins and UI sidecars for Jetski Web and Antigravity using the Sidecar SDK (Node.js, Python, and Go). Use when building custom UI plugins, structuring plugin bundles (plugin.json and sidecar.json), creating interactive auxiliary panes (AuxPane), adaptive styling with host theme CSS variables (--background, --foreground, --primary, --card, etc.), writing backend API routes or frontend pages with preload.js, and integrating with window.sidecar or agentapi.
---

# Developing UI Plugins with Jetski Sidecar SDK

This skill guides you through building, packaging, configuring, and testing interactive **UI plugins** in Jetski Web and Antigravity using the [Sidecar SDK](http://google3/third_party/jetski/sidecar_sdk).

For architectural background and g3docs, see **[go/jetski-ui-plugins](http://goto.google.com/jetski-ui-plugins)** (`devtools/jetski/g3doc/features/agent/ui-plugins.md`), **[go/jetski-agent-plugins](http://goto.google.com/jetski-agent-plugins)** (`devtools/jetski/g3doc/features/agent/agent-plugins.md`), and **[go/jetski-agent-sidecars](http://goto.google.com/jetski-agent-sidecars)** (`devtools/jetski/g3doc/features/agent/agent-sidecars.md`).

---

## What is a UI Plugin?

A **UI plugin** is a plugin bundle containing one or more sidecars with web UI components that serve interactive HTML panels directly inside Jetski and Antigravity. When running, the sidecar hosts a local web server, and the application embeds the web content in a secure iframe inside the conversation's **Auxiliary Pane** (AuxPane).

UI plugins are packaged using the standard Jetski plugin format, allowing them to be installed, discovered, enabled, and shared as a single cohesive unit.

---

## Runtime Compatibility & Supported SDKs

When building a UI plugin, choose your language and SDK based on the target runtime environment:

- **Jetski Internal Web**: Supports **Node.js, Python, and Go** sidecars.
- **External Antigravity App**: Supports **Node.js** sidecars (`SidecarApp` imported from `'sidecar_sdk'`).

---

## Authoritative Templates & SDK Source Code

Refer directly to the official template plugins in google3 for starter project structures, build targets, and setup scripts:

### Starter Template Plugins

- **Node.js Template Plugin**: [third_party/jetski/plugins/templates/node_sdk_plugin](http://google3/third_party/jetski/plugins/templates/node_sdk_plugin)
- **Python Template Plugin**: [third_party/jetski/plugins/templates/python_sdk_plugin](http://google3/third_party/jetski/plugins/templates/python_sdk_plugin)
- **Go Template Plugin**: [third_party/jetski/plugins/templates/go_sdk_plugin](http://google3/third_party/jetski/plugins/templates/go_sdk_plugin)

Each template plugin includes an automated `install.sh` setup script that compiles necessary executables (e.g. Python `.par` or Go binary via Blaze) and installs the bundle into `~/.gemini/config/plugins/<plugin-name>/`.

### Authoritative SDK Implementation Files

- **Sidecar SDK Root**: [third_party/jetski/sidecar_sdk](http://google3/third_party/jetski/sidecar_sdk)
- **Node.js SDK (`SidecarApp`)**: [third_party/jetski/sidecar_sdk/node/index.mjs](http://google3/third_party/jetski/sidecar_sdk/node/index.mjs)
- **Python SDK (`SidecarApp`)**: [third_party/jetski/sidecar_sdk/python/sidecar/main.py](http://google3/third_party/jetski/sidecar_sdk/python/sidecar/main.py)
- **Go SDK (`sidecar.NewApp()`)**: [third_party/jetski/sidecar_sdk/go/sidecar.go](http://google3/third_party/jetski/sidecar_sdk/go/sidecar.go)
- **Frontend Bridge Script (`/preload.js`)**: [third_party/jetski/sidecar_sdk/preload.js](http://google3/third_party/jetski/sidecar_sdk/preload.js)

---

## Plugin Setup & Directory Structure

UI plugins are packaged inside a plugin folder. Place UI sidecars under the `sidecars/<sidecar-id>/` subdirectory:

```text
~/.gemini/config/plugins/<plugin-name>/
├── plugin.json                 # Top-level plugin bundle manifest
├── README.md                   # User-facing documentation
├── assets/                     # Optional assets (e.g. logo.png, logo.svg)
└── sidecars/
    └── <sidecar-id>/           # Sidecar bundle directory
        ├── sidecar.json        # Sidecar manifest ("has_web_ui": true)
        ├── main.mjs            # Backend server (or sidecar.par / compiled binary)
        ├── index.html          # Web UI frontend (/preload.js bridge)
        ├── styles.css          # Host theme-adaptive styles
        └── package.json        # (For Node.js dependencies if needed)
```

### 1. Plugin Manifest (`plugin.json`)
The root `plugin.json` declares the plugin identity and metadata:

```json
{
  "name": "my_ui_plugin",
  "description": "Interactive UI plugin for inspecting and manipulating data in chat.",
  "logo": "assets/logo.svg",
  "suggestedPrompts": [
    "Open the sidecar panel and check connection status",
    "Inspect recent events in the UI viewer",
    "Trigger a sync workflow from the dashboard"
  ]
}
```

- **`name`** *(string, required)*: Unique identifier / display name for the plugin (lowercase kebab-case or snake_case).
- **`description`** *(string, required)*: Brief summary of what the plugin does and who it is for.
- **`logo`** *(string, optional)*: Relative path to a square logo image.
-   **`suggestedPrompts`** *(array of strings, optional)*: Up to 3 starter
    prompts for card and detail views. Exactly 3 prompts are recommended for UI
    card layouts. Empty strings are skipped and additional prompts beyond 3 are
    ignored.

### 2. Sidecar Manifest (`sidecars/<sidecar-id>/sidecar.json`)
The `sidecar.json` file configures process execution, lifecycle policies, and UI views:

```json
{
  "command": "node",
  "args": ["main.mjs"],
  "restart_policy": "always",
  "has_web_ui": true,
  "ui_config": {
    "display_name": "My Custom Panel",
    "views": [
      {
        "path": "/",
        "entrypoint": "SIDECAR_UI_ENTRYPOINT_AUX_PANE",
        "title": "Main View"
      }
    ]
  }
}
```

- **`command` / `args`**: The binary or script to execute. The working directory is the `<sidecar-id>/` folder itself.
- **`restart_policy`**: Set to `"always"` for long-running UI servers.
- **`has_web_ui`**: Must be set to `true` to signal that this sidecar provides a web UI.
- **`ui_config.display_name`**: The primary title displayed at the top of the Auxiliary Pane.
- **`ui_config.views`**: Array of views served by the plugin:
  - `path`: The relative URL path (e.g. `"/"` or `"/index.html"`).
  - `entrypoint`: `"SIDECAR_UI_ENTRYPOINT_AUX_PANE"` to render in the conversation's right-hand side pane.
  - `title`: Label used for tab switching and navigation.

> [!NOTE]
> **Namespaced Sidecar ID**: Sidecars packaged inside a plugin are identified as `<plugin-name>/<sidecar-id>`.

---

## Environment Variables & Runtime Layout

The sidecar runner automatically assigns ports and directories to your process:

- **`ANTIGRAVITY_SIDECAR_WEB_PORT`**: An unused local port assigned to your sidecar. Your HTTP server **must** listen on this port. **Never hardcode port numbers.** (SDK `SidecarApp` handles this automatically).
- **`ANTIGRAVITY_EXECUTABLE_DATA_DIR`**: Absolute path to `<appDataDir>/sidecar_data/<sidecar-id>/data/` for storing persistent files across restarts.
- **Runtime Logs**: Output (`stdout` / `stderr`) is streamed to `<appDataDir>/sidecar_data/<sidecar-id>/logs/sidecar.log`.

> [!WARNING] **The data directory belongs to the sidecar process, not to the
> agents it spawns.** `sidecar_data` is outside the paths an agent can reach by
> default, so an agent asked to write a state file there will fail or stall
> waiting for a permission nobody can grant. If the sidecar and its agent
> exchange files, list the directory in `agent_permissions.workspace_uris` in
> `sidecar.json` as a `file://` URI. See the **automation** skill for the full
> treatment.

---

## Backend Routing (`SidecarApp`)

The Sidecar SDK runtimes (`Node.js`, `Python`, and `Go`) provide a clean, standardized route registration interface:

### 1. HTML Page Routes (`app.page` / `app.Page`)
Registers a `GET` handler that returns an HTML string (`Content-Type: text/html`):

```javascript
// Node.js example
import { SidecarApp } from 'sidecar_sdk';
import fs from 'fs';

const app = new SidecarApp();
app.page('/', () => fs.readFileSync('./index.html', 'utf8'));
await app.start();
```

### 2. JSON API Routes (`app.api` / `app.API`)
Registers an endpoint (`POST` by default, or `"GET"`). Handlers returning objects or dictionaries automatically serialize to JSON (`200 OK`, `application/json`):

```javascript
// Node.js API route
app.api('/api/status', async (req) => {
  return { status: 'ok', uptime: process.uptime() };
});
```

### 3. Serving Static Resources (`.css`, `.js`, Images)
To serve non-HTML resources over `GET`, register a `GET` API handler returning a `Response` instance specifying the exact MIME `contentType`:

- **Node.js**: `new Response(body, { contentType: 'text/css', status: 200 })`
- **Python**: `Response(body=css_bytes, content_type="text/css", status=200)`
- **Go**: `sidecar.Response{Body: cssBytes, ContentType: "text/css", Status: 200}`

```javascript
// Node.js example serving styles.css
app.api('/styles.css', () => {
  return new Response(fs.readFileSync('./styles.css', 'utf8'), {
    contentType: 'text/css',
  });
}, 'GET');
```

### 4. Authentication Rules

- **`GET` Requests**: Universally bypass token authentication so static assets (`.css`, `.js`, images) load cleanly in browser iframes without `401 Unauthorized` errors.
- **`POST` Requests**: Require the `X-Sidecar-Token` header. `preload.js` attaches this header automatically for calls made via `window.sidecar`.

---

## Frontend Bridge (`/preload.js` → `window.sidecar`)

Inject `<script src="/preload.js"></script>` into your HTML `<head>`. This script initializes the iframe bridge, synchronizes theme tokens, and exposes the global `window.sidecar` API:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="/styles.css">
  <script src="/preload.js"></script>
</head>
<body>
  <div class="container">
    <h3>My UI Plugin</h3>
    <button id="send-btn">Send Message to Agent</button>
  </div>
  <script>
    document.getElementById('send-btn').addEventListener('click', async () => {
      if (window.sidecar?.agent) {
        await window.sidecar.agent.sendMessage('Hello from UI plugin!');
      }
    });
  </script>
</body>
</html>
```

### `window.sidecar` API Reference

- **`window.sidecar.conversationId`** *(string | null)*: The currently active conversation ID.
- **`window.sidecar.agent.sendMessage(message, [conversationId])`**: Sends a chat message directly into the conversation.
- **`window.sidecar.agent.startConversation(message)`**: Starts a brand new agent conversation with the given prompt.
- **`window.sidecar.agent.getConversationMetadata(conversationId)`**: Retrieves metadata for a conversation.
- **`window.sidecar.ui.toggleAuxPane({ open?: boolean })`**: Opens, closes, or toggles the auxiliary pane.

---

## Adaptive Theming & Host CSS Variables

Sidecar iframes automatically receive theme updates from the host. When the theme changes, `preload.js` synchronizes **17 root theme tokens** directly onto `document.documentElement`.

### Standard Root Tokens

- **Surfaces**: `--background`, `--content`, `--card`, `--secondary`, `--muted`, `--sidebar`, `--sidebar-secondary`, `--sidebar-muted`
- **Text**: `--foreground`, `--secondary-foreground`, `--muted-foreground`, `--primary-foreground`, `--placeholder`
- **Accents**: `--primary`, `--accent`
- **Borders**: `--border`, `--card-border`

> [!IMPORTANT]
> **Do NOT use `--vscode-*` CSS variables.** Those are legacy passthrough tokens being phased out. Always style with the modern root tokens above.

### Recommended `styles.css` Pattern
Include sensible fallbacks so the UI remains legible when opened directly in a browser (e.g., `http://localhost:<port>` during standalone development):

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--background, #fafafa);
  color: var(--foreground, #333);
  margin: 0;
  padding: 16px;
  line-height: 1.4;
}

.card {
  background: var(--card, #ffffff);
  border: 1px solid var(--card-border, var(--border, #e0e0e0));
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}

.muted-text {
  color: var(--muted-foreground, #666666);
  font-size: 13px;
}

button {
  background: var(--primary, #0e639c);
  color: var(--primary-foreground, #ffffff);
  border: 1px solid var(--border, transparent);
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

/* Hover state: mixing primary toward foreground automatically lightens
   the button in dark mode and darkens it in light mode */
button:hover {
  background: color-mix(in srgb, var(--primary, #0e639c) 88%, var(--foreground, #000));
}

button:active {
  background: color-mix(in srgb, var(--primary, #0e639c) 76%, var(--foreground, #000));
}

pre, code {
  background: var(--secondary, #f5f5f5);
  border: 1px solid var(--border, #e0e0e0);
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
```

---

## Step-by-Step UI Plugin Development Workflow

### Step 1: Initialize Plugin Structure
Choose one of the template plugins (`node_sdk_plugin`, `python_sdk_plugin`, or `go_sdk_plugin`) or create a new directory under `~/.gemini/config/plugins/<plugin-name>/`:

```bash
PLUGIN_DIR=~/.gemini/config/plugins/my_ui_plugin
mkdir -p "$PLUGIN_DIR/sidecars/my_sidecar"
```

Create `plugin.json` at the root and `sidecar.json` under `sidecars/my_sidecar/`.

### Step 2: Implement Backend & Frontend

- Write your backend entrypoint using `SidecarApp` to serve the HTML page and API routes.
- Create `index.html` with `<script src="/preload.js"></script>` and style it with host CSS variables in `styles.css`.

### Step 3: Instruct the user how to enable and test the plugin

1. Open Jetski Web and navigate to the **UI Plugins** tab on the left sidebar.
2. Toggle your plugin to **Enabled**.
3. In any conversation, click the **+** (Plugins) menu in the conversation header to launch your plugin pane in the AuxPane.
4. Check logs at `~/.gemini/sidecar_data/<sidecar-id>/logs/sidecar.log` to troubleshoot runtime issues.
