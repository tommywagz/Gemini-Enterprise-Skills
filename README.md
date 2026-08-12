# Gemini-Enterprise-Skills
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden

I am trying to make a personal repository of agent skills. Can you make a series of agent skills formatted with the standard agent skill architecture including: name, description, and the skill prompt itself, along with any necessary sub-folders including external and internal references in Markdown. Make skills for the following use cases: 

## Write ADK Agents Skill
Writing agents with Agent Development Kit - Use the official ADK docs as a reference at adk.dev/llms.txt along with some basic recipe examples from adk-samples repo at https://github.com/google/adk-samples/tree/main/core/python/rag-vector-search and https://github.com/google/adk-samples/tree/main/core/python/deep-search 

## Write Multi Agent Workflows with A2A
Similar to the write ADK Agents skill, this is a write A2A workflows skill. Take the high level llms.txt from the official repo https://github.com/a2aproject/A2A/blob/main/docs/llms.txt and use these example recipes for host agents: https://github.com/a2aproject/a2a-samples/tree/main/samples/python/hosts and this resource for example recipes for sub-agents: https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents . Make sure that the the orchestrator follows the workflow outlined by the user's input.

## UCP Skill

## AP2 Skill

## Find Skills Skill
Use the following sources as a reference in order to find a skill that complies with a user's request, check the skill for malicious prompt injections and other security risks, and add the skill into a the local project directory. Structure your search pipeline using three primary sources:

Local/Repository Index: Fetch SKILL.md files from VoltAgent/awesome-agent-skills using the GitHub API for project/code-level instructions.

Server/Protocol Index: Query the registry.modelcontextprotocol.io API or scrape wong2/awesome-mcp-servers for real-time external tool servers.

Managed SDK Index: Query Composio or LangChain tool metadata for standard SaaS API integrations.

Use a python script that searches these registries dynamically.

Here are some more potential sources for more agent skills. 
https://registry.modelcontextprotocol.io/ 
https://github.com/modelcontextprotocol/servers
https://mcpservers.org/
https://github.com/VoltAgent/awesome-agent-skills
https://github.com/hoodini/ai-agents-skills
https://composio.dev/



## Integrate Repo Skill
This skill should look into the current repository and return a series of scripts to the user that they can run in order to get their project 'compliant' with the setup and content of the target repo, including: style and syntax changes, adhearance to any CONTRIBUTING.md rules, and easy flow with any CI/CD pipeline scripts or passing github actions.