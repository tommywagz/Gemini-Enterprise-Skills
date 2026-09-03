# Gemini-Enterprise-Skills
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden

I am trying to make a personal repository of agent skills. Can you make a series of agent skills formatted with the standard agent skill architecture including: name, description, and the skill prompt itself, along with any necessary sub-folders including external and internal references in Markdown. 

# Objective
Make agent skills for the following use cases: 

## AP2 Skill
Building agents that can pay, and agent systems where authorization is provable after the fact. Use https://ap2-protocol.org/llms.txt as the high level reference, the spec at https://ap2-protocol.org/ap2/specification/ and https://ap2-protocol.org/ap2/flows/, and the reference implementation at https://github.com/google-agentic-commerce/AP2 (SDK at `code/sdk/python/ap2/`, runnable scenarios at `code/samples/python/scenarios/a2a/human-present` and `.../human-not-present`, each with its own README and `run.sh`). The samples are ADK agents speaking A2A, so this skill set composes directly with the ADK and A2A skills above:

- **Design AP2 Mandate Flows** - Pick and construct the right Verifiable Digital Credentials for the user's goal: Checkout Mandate (open for pre-purchase constraints, closed to authorize a finalized cart) and Payment Mandate (open for delegated autonomous spend, closed to authorize a specific amount against a specific instrument). Covers signing, verification, and what each mandate is and is not allowed to reveal to each party. References https://ap2-protocol.org/ap2/checkout_mandate/ and https://ap2-protocol.org/ap2/payment_mandate/.
- **Choose Human-Present vs. Human-Not-Present Flows** - Decide whether the goal requires real-time user confirmation or delegated autonomous execution under pre-signed constraints, then scaffold the corresponding scenario. This is a routing decision the orchestrator should make before any payment agent is written, because it changes which mandates exist and when they are signed.
- **Implement AP2 Roles as Sub-Agents** - Generate the role-based agents an AP2 transaction needs - Shopping Agent, Merchant Agent, Credentials Provider, Merchant Payment Processor - as A2A-addressable sub-agents with the correct mandate exchange between them. The orchestrator wires them into whatever workflow the user described; this skill guarantees each role only holds the credentials its role is entitled to.
- **Add x402 / Crypto Payment Rails** - Extend a working card-based flow to stablecoin and crypto settlement via x402, using the corresponding sample scenario as the recipe, without changing the mandate structure above it.
- **Audit AP2 Authorization and Privacy** - Review a generated payment system against https://ap2-protocol.org/ap2/security_and_privacy_considerations/ and the agent authorization framework at https://ap2-protocol.org/ap2/agent_authorization/: mandate scoping and expiry, replay protection, credential leakage between roles, and whether the retained evidence is sufficient to resolve a dispute over who authorized what.


## Integrate Repo Skill
This skill should look into the current repository that a coding agent harness is residing along with a target folder or file and return a series of scripts to the user that they can run in order to get their project folder or file mentioned earlier to be 'compliant' with the setup and content of the target repo, including: style and syntax changes, adhearance to any CONTRIBUTING.md rules, and easy flow with any CI/CD pipeline scripts or passing github actions.

## Model Governance Assignment
The objective of this skill is to preview a prompt for an agent or LLM and use up to date reference material spelled out below in order to match the prompt with the ideal model considering the use case, and the preferred amount of token use to intelligence ratio configured by the user. For example, if a user wants to optimize for results, price reduction, or a balance of both with a given task or use case - find a tier of model that aligns closest with that desired configuration. 

Workflow: Once the objective is clear, write an opencode launch command with the configured model and intellignece level with the '--model' tag. This configuration will be outlined by a project or user level opencode.json, with the project level overriding the user level config.

## Real estate floor plan plugin skill
Use a series of MCPs routed via a skill (plugin)
Remote MCP servers from Zillow, apartments.com, and Redfin for research on floor plans

Stage two of the workflow is to have a series of floor plan drawing plugins using Floor Builder and CAD MCP servers. This should be outlined with a skill
