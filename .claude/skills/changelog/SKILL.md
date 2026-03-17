---
name: changelog
description: Generate a grouped changelog from commits since the last version tag and recommend the semver bump type
disable-model-invocation: true
---

# Generate Changelog

Generate a changelog from commits since the last version tag.

## Steps

1. Find the last version tag:

```bash
git describe --tags --abbrev=0
```

2. List all commits since that tag (excluding merges):

```bash
git log <last-tag>..HEAD --oneline --no-merges
```

3. Classify each commit by its conventional commit prefix:
   - `feat!:` or any commit with `BREAKING CHANGE` → **Breaking Changes**
   - `feat:` → **Features**
   - `fix:` → **Bug Fixes**
   - `refactor:` → **Refactoring**
   - `docs:` → **Documentation**
   - `ci:` → **CI/CD**
   - `test:` → **Tests**
   - `chore:` → **Chores**
   - No recognized prefix → **Other**

4. Determine the recommended version bump (first match wins):
   - Any `feat!:` or `BREAKING CHANGE` commit → **major** bump
   - Any `feat:` commit → **minor** bump
   - Otherwise → **patch** bump

5. Calculate the new version number from the current tag (e.g., v1.7.1 + minor → v1.8.0).

## Output Format

```markdown
## v<new-version> (recommended: <bump-type> bump from <current-tag>)

### Breaking Changes
- <commit message> (<short-sha>)

### Features
- <commit message> (<short-sha>)

### Bug Fixes
- <commit message> (<short-sha>)

### Refactoring
- <commit message> (<short-sha>)

### CI/CD
- <commit message> (<short-sha>)

### Documentation
- <commit message> (<short-sha>)

---
Commits since <last-tag>: <count>
Recommended bump: <patch|minor|major> → v<new-version>
```

Only include sections that have commits. Omit empty sections.
