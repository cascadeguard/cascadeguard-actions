# Setup Grype

> Install Anchore Grype vulnerability scanner at a pinned version.

[![CI](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

## Quick start

```yaml
- name: Setup Grype
  uses: cascadeguard/cascadeguard-actions/setup-grype@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
  with:
    version: v0.110.0
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `version` | No | `latest` | Grype version to install (e.g. `v0.110.0`) |
| `install-dir` | No | `/usr/local/bin` | Directory to install the `grype` binary |
| `verify-checksum` | No | `false` | Verify binary checksum with cosign (requires cosign on PATH) |

## Outputs

| Output | Description |
|--------|-------------|
| `version` | Installed Grype version string (e.g. `v0.110.0`) |

## Full workflow example

```yaml
name: Scan image

on:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Grype
        uses: cascadeguard/cascadeguard-actions/setup-grype@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          version: v0.110.0

      - name: Scan image
        run: grype python:3.12-slim --output json > grype-results.json
```

## Supply chain verification

When `verify-checksum: true`, this action downloads the Grype checksums file and verifies it with cosign keyless signatures before installing. Requires `cosign` to be available on the runner.

## Versioning

Pin this action to a full commit SHA for reproducible, auditable pipelines:

```yaml
# Recommended — pinned SHA
uses: cascadeguard/cascadeguard-actions/setup-grype@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67

# Convenience — floating tag (less strict)
uses: cascadeguard/cascadeguard-actions/setup-grype@v1
```