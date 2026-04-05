# Setup Syft

> Install Anchore Syft SBOM generator at a pinned version.

[![CI](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

## Quick start

```yaml
- name: Setup Syft
  uses: cascadeguard/cascadeguard-actions/setup-syft@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
  with:
    version: v1.42.3
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `version` | No | `latest` | Syft version to install (e.g. `v1.42.3`) |
| `install-dir` | No | `/usr/local/bin` | Directory to install the `syft` binary |
| `verify-checksum` | No | `false` | Verify binary checksum with cosign (requires cosign on PATH) |

## Outputs

| Output | Description |
|--------|-------------|
| `version` | Installed Syft version string (e.g. `v1.42.3`) |

## Full workflow example

```yaml
name: Generate SBOM

on:
  push:
    branches: [main]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Syft
        uses: cascadeguard/cascadeguard-actions/setup-syft@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          version: v1.42.3

      - name: Generate SBOM
        run: syft python:3.12-slim --output spdx-json > sbom.spdx.json

      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json
```

## Supply chain verification

When `verify-checksum: true`, this action downloads the Syft checksums file and verifies it with cosign keyless signatures before installing. Requires `cosign` to be available on the runner.

## Versioning

Pin this action to a full commit SHA for reproducible, auditable pipelines:

```yaml
# Recommended — pinned SHA
uses: cascadeguard/cascadeguard-actions/setup-syft@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67

# Convenience — floating tag (less strict)
uses: cascadeguard/cascadeguard-actions/setup-syft@v1
```