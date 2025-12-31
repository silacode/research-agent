---
description: Create a GitHub repository from this local git repo
---

Create a GitHub repository for the current project.

## Steps

1. Ask me whether the repository should be **public** or **private**
2. Determine the repository name from `pyproject.toml` (project.name field) or use the current directory name as fallback
3. Run `gh repo create <repo-name> --source=. --remote=origin --<visibility>` to create the repo
4. Confirm success and show the repository URL
5. Ask me if I want to update this process flow based on any issues encountered or improvements identified

## Execution Notes
- The `gh` command requires full permissions (no sandbox) due to TLS certificate verification issues in the sandbox environment
- Before running, show me the exact command that will be executed and ask for confirmation
- If any hiccup occurs during execution, ask me if I want to update this process flow

## Security Note
The `gh repo create` command only:
- Reads local project files to determine source
- Creates a repository on GitHub under your authenticated account
- Sets the git remote origin
It does NOT execute arbitrary code or access files outside the project.

## Requirements
- The `gh` CLI must be installed and authenticated
- This must be run from within a git repository
