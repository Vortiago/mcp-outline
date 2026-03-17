---
name: version-check
description: Verify that version strings in server.json, plugin.json, marketplace.json, and .mcp.json are all in sync
disable-model-invocation: true
---

# Version Check

Verify all version files are in sync.

## Version Files

Read the version from each of these files:

1. **server.json** — top-level `version` field AND `packages[*].version`
2. **.claude-plugin/plugin.json** — `version` field
3. **.claude-plugin/marketplace.json** — `version` field
4. **.mcp.json** — version embedded in the `args` array (e.g., `"mcp-outline==1.7.1"`)

## Steps

1. Read all 4 files and extract their version strings.

2. Get the latest git tag for comparison:

```bash
git describe --tags --abbrev=0
```

3. Compare all versions against each other.

## Output Format

```
Version Check Results

| Source                     | Version |
|----------------------------|---------|
| server.json (top-level)    | 1.7.1   |
| server.json (packages)     | 1.7.1   |
| .claude-plugin/plugin.json | 1.7.1   |
| .claude-plugin/marketplace | 1.7.1   |
| .mcp.json (args)           | 1.7.1   |
| Latest git tag             | v1.7.1  |

Status: All versions in sync
```

If any version differs, flag the mismatch and suggest the fix:

```
Status: Version mismatch detected!
  - .mcp.json has 1.7.0, expected 1.7.1
  Fix: Run `uv run poe bump-version <correct-version>` to sync all files.
```
