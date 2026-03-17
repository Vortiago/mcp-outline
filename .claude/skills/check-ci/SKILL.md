---
name: check-ci
description: Check GitHub Actions CI status for the current branch, reporting pass/fail for all expected workflows
disable-model-invocation: false
---

# Check CI Status

Check the GitHub Actions CI status for the current branch.

## Steps

1. Get the current commit SHA and branch name:

```bash
git rev-parse HEAD
git branch --show-current
```

2. Fetch all check runs for that commit using the GitHub API:

```bash
gh api "repos/Vortiago/mcp-outline/commits/<SHA>/check-runs" \
  --jq '.check_runs[] | "\(.name)|\(.status)|\(.conclusion)|\(.id)"'
```

3. Report on all expected checks. The full CI suite includes:
   - **Unit Tests** — Python 3.10, 3.11, 3.12, 3.13 (4 runs from `ci.yml`)
   - **CodeQL** — actions + python analyses (2 runs from `codeql.yml`)
   - **E2E Tests** + **E2E Test Report** (2 runs from `e2e.yml`)
   - **Build** (1 run from `ci.yml` or `docker-build.yml`)

4. For any check still `in_progress` or `queued`, report it as pending.

5. For any check with `conclusion: failure`, fetch failure annotations:

```bash
gh api "repos/Vortiago/mcp-outline/check-runs/<CHECK_RUN_ID>/annotations" \
  --jq '.[] | "\(.path):\(.start_line) - \(.message)"'
```

## Output Format

```
CI Status for <short-SHA> on branch <branch-name>

| Check                      | Status      |
|----------------------------|-------------|
| Unit Tests (3.10)          | passed      |
| Unit Tests (3.11)          | passed      |
| Unit Tests (3.12)          | passed      |
| Unit Tests (3.13)          | passed      |
| CodeQL (actions)           | passed      |
| CodeQL (python)            | passed      |
| E2E Tests                  | passed      |
| E2E Test Report            | passed      |
| Build                      | passed      |

Overall: X/Y passed, Z pending, W failed
```

If any checks failed, show the failure annotations below the table.

If no check runs are found, the commit may not have been pushed yet — suggest pushing first.
