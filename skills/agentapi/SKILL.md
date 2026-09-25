---
name: agentapi
description: >-
  How to use the `agentapi` CLI to manage agents - starting new conversations,
  sending messages to conversations, and reading conversation metadata.
  Use this skill when you need to hand work to an agent programmatically rather
  than through a tool call: from a sidecar or automation script, from a shell
  command, from a Python script.
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
