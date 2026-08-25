# A2A Python Multi-Agent Implementation Guide

This guide demonstrates how to build an orchestrating Host Agent using Google ADK that delegates work to remote Sub-Agents over the A2A (Agent2Agent) protocol in Python.

## Table of Contents
- [1. Directory Structure Convention](#1-directory-structure-convention)
- [2. Remote Agent Connections Wrapper](#2-remote-agent-connections-wrapper)
- [3. Orchestrating Host Agent](#3-orchestrating-host-agent)

## 1. Directory Structure Convention

When implementing A2A multi-agent systems, follow this layout:

```
my_multiagent_host/
├── __init__.py                # from . import agent
├── agent.py                   # Exports root_agent = HostAgent(...).create_agent()
├── host_agent.py              # Contains HostAgent definition
└── remote_agent_connection.py # Contains RemoteAgentConnections wrapper
```

---

## 2. Remote Agent Connections Wrapper

The `RemoteAgentConnections` class wraps the A2A SDK's low-level client. It manages connection sessions and translates streaming events into terminal task states.

```python
# remote_agent_connection.py
import traceback
from collections.abc import Callable
from a2a.client import Client, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]

class RemoteAgentConnections:
    """Manages active connections and task delegation to a specific remote agent."""

    def __init__(self, client_factory: ClientFactory, agent_card: AgentCard):
        self.agent_client: Client = client_factory.create(agent_card)
        self.card: AgentCard = agent_card
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(self, message: Message) -> Task | Message | None:
        """Sends a message to the remote agent, returning the final Message or Task status."""
        last_task: Task | None = None
        try:
            async for event in self.agent_client.send_message(message):
                if isinstance(event, Message):
                    return event
                if self.is_terminal_or_interrupted(event[0]):
                    return event[0]
                last_task = event[0]
        except Exception as e:
            print("Exception in A2A send_message:")
            traceback.print_exc()
            raise e
        return last_task

    def is_terminal_or_interrupted(self, task: Task) -> bool:
        """Checks if a task status is terminal or requires user intervention."""
        return task.status.state in [
            TaskState.completed,
            TaskState.canceled,
            TaskState.failed,
            TaskState.input_required,
            TaskState.unknown,
        ]
```

---

## 3. Orchestrating Host Agent

The `HostAgent` serves as the primary router. It is built as a standard Google ADK `Agent` equipped with two crucial tools:
1. `list_remote_agents`: Discovers available sub-agents and their descriptions.
2. `send_message`: Sends user prompts to a selected sub-agent over the A2A protocol.

```python
# host_agent.py
import asyncio
import base64
import json
import os
import uuid
import httpx

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TextPart,
    TransportProtocol,
)
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from remote_agent_connection import RemoteAgentConnections

class HostAgent:
    """The main orchestrating agent that routes and delegates user tasks to remote sub-agents."""

    def __init__(
        self,
        remote_agent_addresses: list[str],
        http_client: httpx.AsyncClient,
    ):
        self.httpx_client = http_client
        config = ClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.client_factory = ClientFactory(config)
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
        
        # Async initialization task to fetch remote agent cards
        loop = asyncio.get_running_loop()
        self._init_task = loop.create_task(self.init_remote_agent_addresses(remote_agent_addresses))

    async def init_remote_agent_addresses(self, remote_agent_addresses: list[str]) -> None:
        """Resolves and registers agent cards for each remote agent address."""
        async with asyncio.TaskGroup() as task_group:
            for address in remote_agent_addresses:
                task_group.create_task(self.retrieve_card(address))

    async def retrieve_card(self, address: str) -> None:
        """Fetches an agent card from `address` and registers it."""
        card_resolver = A2ACardResolver(self.httpx_client, address)
        card = await card_resolver.get_agent_card()
        self.register_agent_card(card)

    def register_agent_card(self, card: AgentCard) -> None:
        """Registers a remote agent card for delegation."""
        remote_connection = RemoteAgentConnections(self.client_factory, card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = [json.dumps({"name": ra["name"], "description": ra["description"]}) 
                      for ra in self.list_remote_agents()]
        self.agents = '\n'.join(agent_info)

    def create_agent(self) -> Agent:
        """Builds the underlying Google ADK agent for the host."""
        litellm_model = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.5-flash')
        return Agent(
            model=LiteLlm(model=litellm_model),
            name='host_agent',
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                'This agent orchestrates the decomposition of the user request into'
                ' tasks that can be performed by the child agents.'
            ),
            tools=[
                self.list_remote_agents,
                self.send_message,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        """Renders the root instruction prompt for the host agent."""
        current_agent = self.check_state(context)
        return f"""You are an expert delegator that can delegate the user request to the
appropriate remote agents.

Discovery:
- You can use `list_remote_agents` to list the available remote agents you
can use to delegate the task.

Execution:
- For actionable requests, you can use `send_message` to interact with remote agents to take action.

Be sure to include the remote agent name when you respond to the user.

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

Agents:
{self.agents}

Current active agent: {current_agent['active_agent']}
"""

    def check_state(self, context: ReadonlyContext) -> dict[str, str]:
        """Returns the currently active agent for the session, if any."""
        state = context.state
        if (
            'context_id' in state
            and 'session_active' in state
            and state['session_active']
            and 'agent' in state
        ):
            return {'active_agent': f'{state["agent"]}'}
        return {'active_agent': 'None'}

    def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: object,
    ) -> None:
        """Marks the session as active before the first model call."""
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            state['session_active'] = True

    def list_remote_agents(self) -> list[dict[str, str]]:
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []
        return [
            {'name': card.name, 'description': card.description} for card in self.cards.values()
        ]

    async def send_message(self, agent_name: str, message: str, tool_context: ToolContext) -> list:
        """Sends a message/task to a specified remote agent.

        Args:
          agent_name: The name of the agent to send the task to.
          message: The message/task content to send.
          tool_context: The ADK tool context running this command.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        
        state = tool_context.state
        state['agent'] = agent_name
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f'Client not available for {agent_name}')
            
        task_id = state.get('task_id', None)
        context_id = state.get('context_id', None)
        message_id = state.get('message_id', None)
        
        if not message_id:
            message_id = str(uuid.uuid4())

        request_message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=message))],
            message_id=message_id,
            context_id=context_id,
            task_id=task_id,
        )
        
        response = await client.send_message(request_message)
        if isinstance(response, Message):
            return await convert_parts(response.parts, tool_context)
            
        task: Task = response
        state['session_active'] = task.status.state not in [
            TaskState.completed,
            TaskState.canceled,
            TaskState.failed,
            TaskState.unknown,
        ]
        if task.context_id:
            state['context_id'] = task.context_id
        state['task_id'] = task.id
        
        if task.status.state == TaskState.input_required:
            tool_context.actions.skip_summarization = True
            tool_context.actions.escalate = True
        elif task.status.state == TaskState.canceled:
            raise ValueError(f'Agent {agent_name} task {task.id} was cancelled')
        elif task.status.state == TaskState.failed:
            raise ValueError(f'Agent {agent_name} task {task.id} failed')
            
        response_parts = []
        if task.status.message:
            response_parts.extend(await convert_parts(task.status.message.parts, tool_context))
        if task.artifacts:
            for artifact in task.artifacts:
                response_parts.extend(await convert_parts(artifact.parts, tool_context))
                
        return response_parts

async def convert_parts(parts: list[Part], tool_context: ToolContext) -> list:
    """Converts a list of A2A Parts into ADK-friendly representations."""
    return [await convert_part(p, tool_context) for p in parts]

async def convert_part(part: Part, tool_context: ToolContext) -> object:
    """Converts a single A2A Part into an ADK-friendly representation."""
    if part.root.kind == 'text':
        return part.root.text
    if part.root.kind == 'data':
        return part.root.data
    if part.root.kind == 'file':
        # Repackage A2A FilePart to Google GenAI Blob
        file_id = part.root.file.name
        file_bytes = base64.b64decode(part.root.file.bytes)
        file_part = types.Part(
            inline_data=types.Blob(mime_type=part.root.file.mime_type, data=file_bytes)
        )
        await tool_context.save_artifact(file_id, file_part)
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        return DataPart(data={'artifact-file-id': file_id})
    return f'Unknown type: {part.kind}'
```
