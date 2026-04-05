# scan-issues

> Create or update GitHub Issues from Grype/Trivy scan results.

[![CI](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

## Quick start

```yaml
- name: Create CVE issues
  uses: cascadeguard/cascadeguard-actions/scan-issues@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
  with:
    grype-results: grype-results.json
    image: alpine
    tag: '3.20'
    repo: ${{ github.repository }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `grype-results` | No\* | — | Path to Grype JSON results file |
| `trivy-results` | No\* | — | Path to Trivy JSON results file |
| `image` | Yes | — | Image name (e.g. `alpine`, `python-3.12-slim`) |
| `tag` | No | — | Image tag that was scanned |
| `repo` | Yes | — | GitHub repository (`owner/repo`) for issue management |
| `github-token` | Yes | — | GitHub token with issue write access |
| `cascadeguard-version` | No | `main` | CascadeGuard CLI git ref to install |

\* At least one of `grype-results` or `trivy-results` must be provided.

## Outputs

| Output | Description |
|--------|-------------|
| `created` | Number of new issues created |
| `updated` | Number of existing issues updated |
| `reopened` | Number of closed issues reopened |

## Full workflow example

```yaml
name: Scan and track CVEs

on:
  schedule:
    - cron: '0 6 * * *'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Grype
        uses: cascadeguard/cascadeguard-actions/setup-grype@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          version: v0.110.0

      - name: Scan image
        run: grype python:3.12-slim --output json > grype-results.json

      - name: Create or update CVE issues
        id: issues
        uses: cascadeguard/cascadeguard-actions/scan-issues@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          grype-results: grype-results.json
          image: python
          tag: 3.12-slim
          repo: ${{ github.repository }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Summary
        run: |
          echo "Created: ${{ steps.issues.outputs.created }}"
          echo "Updated: ${{ steps.issues.outputs.updated }}"
          echo "Reopened: ${{ steps.issues.outputs.reopened }}"
```

## Issue lifecycle

This action manages CVE issues automatically:

- **Creates** a new issue for each new Critical or High CVE
- **Updates** an existing open issue when the CVE is still present in a new scan
- **Reopens** a closed issue if the same CVE reappears after a rebuild

Issues are idempotent — re-running on the same results will not create duplicates.

## Versioning

Pin this action to a full commit SHA for reproducible, auditable pipelines:

```yaml
# Recommended — pinned SHA
uses: cascadeguard/cascadeguard-actions/scan-issues@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67

# Convenience — floating tag (less strict)
uses: cascadeguard/cascadeguard-actions/scan-issues@v1
```