# scan-report

> Parse Grype and/or Trivy scan results into a structured vulnerability report.

[![CI](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

## Quick start

```yaml
- name: Generate vulnerability report
  uses: cascadeguard/cascadeguard-actions/scan-report@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
  with:
    grype-results: grype-results.json
    image: python
    output-dir: reports/
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `grype-results` | No\* | — | Path to Grype JSON results file |
| `trivy-results` | No\* | — | Path to Trivy JSON results file |
| `image` | Yes | — | Image name for report metadata (e.g. `python-3.12-slim`) |
| `output-dir` | Yes | — | Directory to write `vulnerability-report.json` and `.md` |
| `cascadeguard-version` | No | `main` | CascadeGuard CLI git ref to install |

\* At least one of `grype-results` or `trivy-results` must be provided.

## Outputs

| Output | Description |
|--------|-------------|
| `report-json` | Path to the generated JSON report |
| `report-md` | Path to the generated Markdown report |
| `total-cves` | Total number of CVEs found |
| `critical-count` | Number of critical CVEs |
| `high-count` | Number of high CVEs |

## Full workflow example

```yaml
name: Scan and report

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

      - name: Generate report
        id: report
        uses: cascadeguard/cascadeguard-actions/scan-report@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          grype-results: grype-results.json
          image: python-3.12-slim
          output-dir: reports/

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: vulnerability-report
          path: reports/

      - name: Fail on critical CVEs
        if: steps.report.outputs.critical-count > 0
        run: |
          echo "::error::${{ steps.report.outputs.critical-count }} critical CVEs found"
          exit 1
```

## Report format

The action generates two files in `output-dir`:

- **`vulnerability-report.json`** — machine-readable report with full CVE details, CVSS scores, and fix availability
- **`vulnerability-report.md`** — human-readable Markdown suitable for GitHub Job Summaries or PR comments

## Versioning

Pin this action to a full commit SHA for reproducible, auditable pipelines:

```yaml
# Recommended — pinned SHA
uses: cascadeguard/cascadeguard-actions/scan-report@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67

# Convenience — floating tag (less strict)
uses: cascadeguard/cascadeguard-actions/scan-report@v1
```