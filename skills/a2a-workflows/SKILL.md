---
name: a2a-workflows
description: "Skill for authoring A2A (Agent2Agent) multi-agent workflows, featuring host-agent orchestration and sub-agent communication. TRIGGER when: 'A2A workflow', 'A2A multi-agent', 'A2A host', 'A2A sub-agent', 'Agent2Agent collaboration', 'AgentCard', 'agent-card.json', 'A2ACardResolver'. DO NOT TRIGGER when: normal ADK workflows without A2A (use google-agents-cli-adk-code)."
version: 1.0.0
author: Google
tags: [a2a, adk, python, multi-agent]
license: Apache-2.0
compatibility: google-adk >= 2.0.0
metadata: {}
---

- Overview
The Agent2Agent (A2A) protocol is an open standard designed to enable interoperability between disparate AI systems. It allows agents built on different frameworks to discover, negotiate, and collaborate on tasks securely.
This skill guides the design and implementation of an orchestrating "Host Agent" using the Google Agent Development Kit (ADK) that delegates work dynamically to remote "Sub-Agents" via the A2A protocol.

- Prerequisites
- Python >= 3.12
- `google-adk[a2a]` installed.
- Target remote agents must expose an `AgentCard` at `/.well-known/agent-card.json` and accept A2A RPC endpoints (e.g., `SendMessage`, `GetTask`).

- Workflow

- Step 1: Initialize Project Structure
Ensure your project contains the standard multi-agent package layout:
- `app/remote_agent_connection.py` (A2A client wrap logic)
- `app/host_agent.py` (HostAgent wrapper logic)
- `app/agent.py` (Exports the instanced root ADK agent)

- Step 2: Implement A2A Remote Connections
Inside `app/remote_agent_connection.py`, create a class to manage low-level A2A sessions.
- Use `a2a.client.ClientFactory` to spawn connection clients from retrieved `AgentCard` specifications.
- Keep track of A2A task states like `TaskState.completed`, `TaskState.input_required`, `TaskState.failed`.
- Refer to `references/a2a-multiagent-python.md` Section 2 for the complete boilerplate.

- Step 3: Implement Host Agent Orchestration
Inside `app/host_agent.py`, define the orchestrating `HostAgent`.
- Run an asynchronous task `init_remote_agent_addresses` during boot to dynamically resolve the remote cards using `a2a.client.A2ACardResolver`.
- Build the core ADK `Agent` equipped with two tools:
  1. `list_remote_agents`: Queries and displays all available remote sub-agents with their names and descriptions.
  2. `send_message`: Sends prompts and tracks execution of remote tasks.
- Refer to `references/a2a-multiagent-python.md` Section 3 for the complete boilerplate.

- Step 4: Wire Tools & Handle Task Progression
Within the `send_message` tool:
- Dynamically track task state via the ADK `ToolContext` state dict (`context_id`, `task_id`, `message_id`).
- Check the sub-agent task state after calls. If `TaskState.input_required`, set `tool_context.actions.escalate = True` and `tool_context.actions.skip_summarization = True` to halt execution and return control to the parent or user.
- If `TaskState.failed` or `TaskState.canceled`, raise an appropriate `ValueError` to allow ADK's error-handling flows to recover or report the failure.

- Step 5: Convert and Extract Artifacts
Convert all returned A2A message parts into ADK-friendly types:
- **Text Parts:** Return directly.
- **Data/Form Parts:** Return as raw JSON dictionaries.
- **File Parts:** Decode base64 payloads and save using `await tool_context.save_artifact(file_id, file_part)`. Set `escalate = True` and `skip_summarization = True`.

- Examples

- Example 1: Orchestration Prompt Example
Input: "Delegate the audit report task to the specialist expense agent."
Expected output / behavior:
1. The Host Agent calls `list_remote_agents` to discover active cards:
   ```json
   [{"name": "expense_reimbursement", "description": "Audits expense reports and generates summaries."}]
   ```
2. The Host Agent selects `expense_reimbursement` and calls:
   ```python
   await send_message(agent_name="expense_reimbursement", message="Review audit report...")
   ```
3. The tool tracks task updates over A2A and streams the result back to the host, who then reports the final success message to the user.

- Error Handling
- **Sub-Agent Down or HTTP Timeout:** If connection or resolution fails during `retrieve_card`, catch the `httpx.HTTPError` gracefully. Log the failure and continue with remaining active sub-agents.
- **Sub-Agent Task Failure:** Always catch `TaskState.failed` in `send_message` and raise a descriptive `ValueError` containing the sub-agent's error reason so the LLM or user is informed.

- Input Validation
- **Remote Addresses:** Validate remote agent addresses before calling `A2ACardResolver`. Ensure they are valid URLs/domains and conform to safety specifications to prevent Server-Side Request Forgery (SSRF).
- **Sub-Agent Cards:** Check that retrieved `AgentCard` schema fields (e.g. `name`, `description`) are non-empty and safe before registration.

- Anti-Patterns
- **Synchronous Blocking HTTP Calls:** Never make synchronous or blocking network calls inside tools or background tasks, as this blocks the ADK event loop. Always use `httpx.AsyncClient`.
- **Static Host Configuration:** Avoid hardcoding child agent capabilities or endpoints statically. Use `A2ACardResolver` to resolve details dynamically via `.well-known/agent-card.json`.
- **Missing Error Boundaries:** Do not let a single failed remote agent connection crash the entire host orchestrator during startup or delegation. Catch and handle exceptions gracefully.

- Fallback Instructions
- **Reference Offline Fallback:** If reference files (`references/a2a-spec.md` or `references/a2a-multiagent-python.md`) are unavailable, refer to standard ADK orchestration tutorials or look up the general A2A specification protocol. You can construct custom communication wrappers around A2A RPC endpoints manually using the standard ADK `Workflow` API or custom `Tool` definitions.

- Reference Files
- **references/a2a-spec.md**: A2A protocol core objects (AgentCard, Task, Message, Artifact) and RPC methods.
- **references/a2a-multiagent-python.md**: Detailed Python code boilerplate for `RemoteAgentConnections` and the orchestrating `HostAgent`.

- Output Format
This skill produces a fully functional, A2A-compliant, multi-agent host orchestrator. The resulting python code must compile with no syntax errors and conform to the file structure described in `references/a2a-multiagent-python.md`.
