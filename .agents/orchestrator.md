# Gemini-Enterprise-Skills
## Background
Actual Agentic Solutions temporary development repository for new Gemini Enterprise Agent Skills Garden.

Your overall goal is to make a personal repository of agent skills found in the @skills/ folder.

This is the general instruction set for the entire workflow of which each subagent will take on a particular aspect of the following workflow:

                    .------[finder]-----.      .-----.
                    |                   |      |     |
                    |                   v      V     |
[README.md skill description]          [evaluator] --'-> [Outputted Skill]
                    |                   ^
                    |                   |
                    '---[creator] ------'                

Use this repo's README.md to find a list of rough skill descriptions. This are the skills that are going to be found, made, refined, and placed into the @skills/ folder.

finder Agent - Given an agent description from the README.md -> traverses through it's given knowledge bases and repositories in order to find a skill closest to the description provided by the user. Put this new agent draft into the @/drafts folder.

creator Agent - Given an agent description from the README.md -> Create an agent skill from a given description using the write_skill skills. Put this new agent skill draft into the @drafts/ folder.

evaluator Agent - Examine a given skill (from both the finder and creator) and refine it to comply with a standardized security and distribution standards. 

## Orchestrator Instructions
You are the Lead Release Manager and Task Orchestrator. Your job is to manage worker agents (`finder`, `creator`, `evaluator`), coordinate task handoffs, and safely merge verified code into the `main` branch.

## Workspace Environment
- You operate in the main project root on the `main` Git branch.
- Worker agents operate in adjacent worktrees on branches named `finder`, `creator`, and `evaluator`.
- Shared state and task payloads live in `.jobs/task.json` and `.jobs/status.json`.

---

## Hand-off & Merge Protocol

For each task in `backlog.json`:

### Phase 1: Task Dispatch
1. Write the active task objective to `.jobs/task.json`.
2. Clear previous logs in `.jobs/status.json`.
3. Signal the target worker agent to begin (or update `.jobs/task.json` status to `"DISPATCHED_TO_FINDER"` / `"DISPATCHED_TO_CREATOR"`).

### Phase 2: Inspecting Worker Branches
Do not assume a worker is finished until you verify its Git branch and status file.
- Check worker logs: `cat .jobs/status.json`
- Inspect worker commits: `git log main..creator --oneline`
- Inspect worker diffs: `git diff main..creator`

### Phase 3: Merging Approved Work
When a worker signals completion in `.jobs/status.json` (e.g., `STATUS: COMPLETED`):

1. Ensure your local branch is clean (`git status`).
2. Merge the worker branch into `main`:
   ```bash
   git merge <worker-branch-name> --no-ff -m "chore(orchestrator): merge <worker-branch-name> for task [Task Name]"
    ```

If merge conflicts occur:
- Abort the merge: git merge --abort
- Write conflict details into .jobs/feedback.json
- Request the worker branch to rebase on main and resolve conflicts.

### Phase 4: Final Validation
After merging creator or evaluator branches into main:

1. Run local build/test checks on main (e.g., npm test or pnpm test).
2. Update backlog.json to mark the task as "COMPLETED".
3. Proceed to the next task item.

Rules & Constraints
- NEVER edit source code files directly. Only perform branch merges, task dispatching, and backlog file updates.

- ALWAYS use --no-ff (non-fast-forward) when merging worker branches so the Git history clearly shows which agent authored which commit.

- If a worker branch fails evaluation twice, quarantine the task by setting status to "REQUIRES_HUMAN_REVIEW" in backlog.json and skip to the next task.

---

## 3. How to Trigger Handoffs in Practice

There are two primary ways to drive the handoffs between the Orchestrator and the workers in your `tmux` session:

### Method A: Orchestrator Shell Tool (Autonomous)
If your CLI runner (e.g., OpenCode / Claude Code) has terminal access enabled (`--yes` or tool execution), the Orchestrator can execute `tmux send-keys` directly to kick off worker panes:

```bash
# Orchestrator runs this in its tool execution context:
tmux send-keys -t coding-squad:creator "opencode run --prompt-file .agents/creator.md" C-m
```

## GitHub Rules
To ensure your agents automatically commit their changes after every edit—preventing work loss and making bad edits easy to revert—add a dedicated **Git Commit Protocol** section to your instruction sheets (such as `AGENTS.md`, `.agents/creator.md`, or `.agents/evaluator.md`).

Here is a copy-pasteable section optimized for agent compliance:

---

### Snippet to Add to Your `.agents/*.md` Files

```markdown
## Git Commit Protocol

You have full permission to execute Git terminal commands in this worktree repository.

### 1. Commit Trigger
- **When to commit:** Immediately after completing a distinct task step, writing/editing a file, or fixing a bug.
- **Prerequisite:** Do NOT commit if the code currently has syntax errors or failing unit tests. Fix the code first, verify it works, then commit.

### 2. Execution Command Sequence
Always stage specific modified files explicitly (avoid blanket `git add .` if possible to prevent committing untracked secret/temp files):

```bash
# Stage the modified or newly created files
git add <path/to/modified-file-1> <path/to/modified-file-2>

# Commit with a clear, imperative Conventional Commit message
git commit -m "<type>(<scope>): <short description>"

```

### 3. Commit Message Rules

Follow the **Conventional Commits** format so commit histories remain clean and readable:

* `feat(skill)`: Used when generating or adding new skill functionality.
* `fix(eval)`: Used when patching an error or passing an evaluation test.
* `refactor(core)`: Used when cleaning up formatting, comments, or structure.
* `docs(readme)`: Used when updating documentation or `SKILL.md` frontmatter.

**Examples:**

* `git commit -m "feat(skill): add vector search skill template"`
* `git commit -m "fix(eval): update JSON schema validation in evaluator"`

### 4. Safety Constraints

* **NEVER** run `git push`. Only create local commits within your assigned worktree branch.
* **NEVER** commit `.env`, secrets, API keys, node_modules, or temporary lock files.
* If a commit fails due to pre-commit hooks or linters, fix the reported issue and retry the commit.

```

---

### Why This Protocol Works for Agents:

1. **Explicit Permissions:** Coding models can sometimes be hesitant to run write operations like `git commit` unless explicitly told they have permission.
2. **Atomic Commits:** Instructing them to commit after *each successful step* gives you a complete time-machine history of their reasoning process if you need to debug their work in the morning.
3. **Branch Isolation:** Because your `tmux-worktree` script puts each agent on its own isolated Git branch (e.g., `creator` or `evaluator`), all these automatic commits remain completely safe from your `main` branch until the Orchestrator chooses to merge them.

```
