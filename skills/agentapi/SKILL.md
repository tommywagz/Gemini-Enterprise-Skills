---
name: agentapi
description: >-
  How to use the `agentapi` CLI to manage agents - starting new conversations,
  sending messages to conversations, and reading conversation metadata.
  Use this skill when you need to hand work to an agent programmatically rather
  than through a tool call: from a sidecar or automation script, from a shell
  command, from a Python script. Includes health check probing, retry backoff,
  and safe prompt parameter sanitization.
disable-slash-command: true
---

# Agent API

`agentapi` is a CLI that talks to the running language server, so anything that
can run a shell command can drive the agent. Use it when the caller is *not* the
agent itself, for example from a sidecar.

## Discovering commands

The CLI is self-documenting, and its help output is generated from the live
command registry.

```bash
agentapi help            # every command, with usage
agentapi <command> help  # description and examples for one command
```

## Common usage

```bash
# Start a new conversation with a prompt.
agentapi new-conversation "Summarize my unread email and flag anything urgent"

# Send a message to another conversation, or to your own to notify yourself.
agentapi send-message "<conversation-id>" "Build finished, results are in /tmp/out"

# Read metadata for a conversation.
agentapi get-conversation-metadata "<conversation-id>"
```

## Connection Resilience & Error Recovery

When invoking `agentapi` from an automation script or sidecar process, the language server might still be initializing or temporarily unavailable, resulting in `connection refused` errors. Implement health probing and exponential backoff retry logic:

1. **Health check probe**: Verify the language server endpoint is responsive before issuing CLI commands:
   ```bash
   : "${ANTIGRAVITY_LS_ADDRESS:=localhost:5387}"
   curl -sS "http://${ANTIGRAVITY_LS_ADDRESS}/healthz"
   # or probe directly:
   curl -f -sS "http://localhost:5387/healthz" > /dev/null 2>&1
   ```

2. **Exponential backoff retry loop**: Wrap CLI invocations with a retry loop to tolerate transient restarts:
   ```bash
   wait_for_server() {
     local max_attempts=5
     local delay=1
     local attempt=1
     local endpoint="http://${ANTIGRAVITY_LS_ADDRESS:-localhost:5387}/healthz"

     while [ "$attempt" -le "$max_attempts" ]; do
       if curl -s -f "$endpoint" > /dev/null 2>&1; then
         return 0
       fi
       echo "Language server not ready at $endpoint (attempt $attempt/$max_attempts). Retrying in ${delay}s..."
       sleep "$delay"
       delay=$((delay * 2))
       attempt=$((attempt + 1))
     done
     echo "Error: Language server unreachable at $endpoint after $max_attempts attempts." >&2
     return 1
   }
   ```

## Security & Input Sanitization (Shell Injection Prevention)

Dynamic external input (e.g. from webhooks, user forms, or external logs) passed to `agentapi` commands must never be naively interpolated directly into shell strings.

1. **Never use unescaped string interpolation**:
   Passing unescaped string interpolations into shell commands (e.g. `sh -c "agentapi new-conversation \"$USER_INPUT\""` or `eval`) creates severe shell injection vulnerabilities where untrusted characters (`;`, `|`, `` ` ``, `$()`) execute arbitrary host commands.

2. **Safe parameter passing via files or quoted arguments**:
   Pass arguments as discrete parameters without shell re-evaluation, or write prompt content to a temporary file:
   ```bash
   # Safe: Pass arguments as discrete parameters with strict double-quoting
   agentapi new-conversation -- "$USER_INPUT"

   # Safe: Passing multiline or untrusted content via temporary file
   PROMPT_FILE=$(mktemp)
   printf '%s' "$USER_INPUT" > "$PROMPT_FILE"
   agentapi new-conversation -- "$(cat "$PROMPT_FILE")"
   rm -f "$PROMPT_FILE"
   ```
