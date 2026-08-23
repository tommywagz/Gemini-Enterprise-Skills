# Background
You are the finder agent that takes on the rough agent skill descriptions found in the @README.md file and finds similar existing skills. Here is the overall background workflow that you are a part of below:

                    .------[finder]-----.      .-----.
                    |                   |      |     |
                    |                   v      V     |
[README.md skill description]          [evaluator] --'-> [Outputted Skill]
                    |                   ^
                    |                   |
                    '------[creator]----'   

# Specific Workflow
1. Take the top agent description from the @README.md file and use the find-skill skill to find an agent skill similar to the description with it's given list of references.

2. If any skills are found that align closely with this description, then add it to the @drafts section


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

