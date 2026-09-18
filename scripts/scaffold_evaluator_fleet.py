#!/usr/bin/env python3
"""Scaffold the Multi-Agent Evaluation Fleet for Jetski / Antigravity / OpenCode.

This script sets up git worktrees, branches, and symlinked coordination directories
for the 6 parallel evaluator workers and 1 orchestrator agent, without executing the agents.

Usage:
  python3 scripts/scaffold_evaluator_fleet.py [--check-only] [--clean]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_DIR = ROOT / "jobs"
CONFIG_FILE = ROOT / "opencode.json"
NUM_WORKERS = 6


def run_cmd(cmd: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=check)


def check_prerequisites():
    print("🔍 Checking prerequisites...")
    git_branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if git_branch != "main":
        print(f"⚠️  Warning: Current branch is '{git_branch}', expected 'main'.", file=sys.stderr)
    else:
        print("  ✓ On branch 'main'")

    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")
    print("  ✓ opencode.json present")

    # Check token efficiency linter
    linter = run_cmd(["python3", "scripts/validate_skill_token_efficiency.py"], check=False)
    if linter.returncode == 0:
        print("  ✓ validate_skill_token_efficiency.py passed")
    else:
        print(f"  ❌ Token efficiency linter failed:\n{linter.stderr}")


def setup_worktrees():
    print(f"\n📁 Setting up isolated worktrees for {NUM_WORKERS} evaluator workers...")
    worktree_list = run_cmd(["git", "worktree", "list", "--porcelain"]).stdout

    for i in range(1, NUM_WORKERS + 1):
        worker_id = f"evaluator-{i}"
        branch_name = f"agent-{worker_id}"
        worktree_path = ROOT.parent / f"Gemini-Enterprise-Skills-{worker_id}"

        # Check if worktree or branch already exists
        if str(worktree_path) in worktree_list:
            print(f"  ✓ Worktree for {worker_id} already registered at: {worktree_path}")
        else:
            # Check if branch exists
            branch_check = run_cmd(["git", "rev-parse", "--verify", branch_name], check=False)
            if branch_check.returncode == 0:
                print(f"  - Attaching existing branch '{branch_name}' to worktree at {worktree_path}...")
                run_cmd(["git", "worktree", "add", str(worktree_path), branch_name])
            else:
                print(f"  - Creating new branch '{branch_name}' and worktree at {worktree_path}...")
                run_cmd(["git", "worktree", "add", "-b", branch_name, str(worktree_path), "main"])

        # Ensure jobs symlink exists in worker worktree
        worker_jobs = worktree_path / "jobs"
        if not worker_jobs.exists():
            print(f"  - Symlinking {JOBS_DIR} -> {worker_jobs}...")
            os.symlink(JOBS_DIR, worker_jobs)
        else:
            print(f"  ✓ jobs symlink exists for {worker_id}")


def verify_fleet_scaffolding():
    print("\n🔍 Verifying fleet scaffolding and communications bus...")
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    agents = config.get("agents", {})
    if "orchestrator" not in agents:
        print("  ❌ 'orchestrator' not defined in opencode.json")
    else:
        print("  ✓ Orchestrator agent configured")

    missing_workers = [f"evaluator-{i}" for i in range(1, NUM_WORKERS + 1) if f"evaluator-{i}" not in agents]
    if missing_workers:
        print(f"  ❌ Missing worker agents in config: {missing_workers}")
    else:
        print(f"  ✓ All {NUM_WORKERS} evaluator workers configured in opencode.json")

    # Check inboxes & statuses
    for i in range(1, NUM_WORKERS + 1):
        inbox = JOBS_DIR / "inbox" / f"evaluator-{i}.json"
        status = JOBS_DIR / "status" / f"evaluator-{i}.json"
        prompt_file = ROOT / f".agents/worker-evaluator-{i}.md"
        assert inbox.is_file(), f"Missing inbox: {inbox}"
        assert status.is_file(), f"Missing status: {status}"
        assert prompt_file.is_file(), f"Missing prompt file: {prompt_file}"

    print(f"  ✓ All inboxes, status files, and prompt templates verified for evaluator-1..{NUM_WORKERS}")

    with open(JOBS_DIR / "backlog.json") as f:
        backlog = json.load(f)
    print(f"  ✓ Master backlog loaded: {len(backlog.get('tasks', []))} tasks queued for evaluation.")


def print_fleet_launch_instructions():
    print("\n" + "=" * 72)
    print("🚀 FLEET SCAFFOLDING COMPLETE (Execution paused as requested)")
    print("=" * 72)
    print("\nWhen you are ready to launch the fleet, execute the following commands:\n")
    print("1. Start a dedicated tmux multi-pane session:")
    print("   tmux new-session -s skills-fleet -n orchestrator")
    print()
    print("2. In the Orchestrator pane (main repository root):")
    print("   opencode run orchestrator")
    print()
    print("3. In parallel worker panes (one for each worktree):")
    for i in range(1, NUM_WORKERS + 1):
        worker_id = f"evaluator-{i}"
        worktree_path = ROOT.parent / f"Gemini-Enterprise-Skills-{worker_id}"
        print(f"   # Worker {i}:")
        print(f"   cd {worktree_path} && opencode run {worker_id}")
    print()
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Scaffold the multi-agent evaluator fleet.")
    parser.add_argument("--check-only", action="store_true", help="Only verify existing scaffolding without creating worktrees")
    args = parser.parse_args()

    check_prerequisites()
    if not args.check_only:
        setup_worktrees()
    verify_fleet_scaffolding()
    print_fleet_launch_instructions()


if __name__ == "__main__":
    main()
