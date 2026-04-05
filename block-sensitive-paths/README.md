# block-sensitive-paths

A reusable GitHub Actions composite action that **rejects pull requests** containing
files in private/internal directories that must not appear in public repositories.

## Features

- Configurable list of blocked path patterns (directory prefixes and exact filenames)
- Runs on PR events; fails the check with a clear message listing each blocked file
- Handles large PRs via paginated GitHub API calls
- Emits per-file `::error::` annotations so violations are highlighted in the PR diff
- Zero external dependencies — pure bash + `gh` CLI (available on all GitHub-hosted runners)

## Usage

```yaml
name: PR Path Guard
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  block-sensitive-paths:
    name: Block sensitive paths
    runs-on: ubuntu-latest
    steps:
      - name: Block sensitive paths
        uses: cascadeguard/cascadeguard-actions/block-sensitive-paths@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Custom blocked paths

```yaml
      - name: Block sensitive paths
        uses: cascadeguard/cascadeguard-actions/block-sensitive-paths@main
        with:
          blocked-paths: |
            .ai/
            docs/plans/
            artifacts/
            internal/
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `blocked-paths` | No | `.ai/` `docs/plans/` `artifacts/` | Newline-separated path patterns. Trailing `/` matches a directory prefix; no trailing `/` matches an exact filename. |
| `github-token` | No | `${{ github.token }}` | Token for the GitHub REST API to list PR files. |

## Branch protection setup

After enabling the action in a repo, add `Block sensitive paths` as a required status
check in **Settings → Branches → Branch protection rules** to prevent merging blocked PRs.

## Pattern matching rules

- `".ai/"` — matches any file whose path starts with `.ai/` (e.g. `.ai/steering/foo.md`)
- `"docs/plans/"` — matches any file under `docs/plans/`
- `"secret.txt"` — exact filename match only
