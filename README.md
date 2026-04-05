# cascadeguard-actions

Reusable composite GitHub Actions for CascadeGuard security workflows.

[![CI](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml/badge.svg)](https://github.com/cascadeguard/cascadeguard-actions/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Security-first:** Pin all action references to a full commit SHA for reproducible, auditable pipelines.

## Actions

| Action | Description | Docs |
|--------|-------------|------|
| [`setup-grype`](./setup-grype/) | Install Anchore Grype vulnerability scanner at a pinned version | [README](./setup-grype/README.md) |
| [`setup-syft`](./setup-syft/) | Install Anchore Syft SBOM generator at a pinned version | [README](./setup-syft/README.md) |
| [`scan-report`](./scan-report/) | Parse Grype/Trivy results into a structured vulnerability report | [README](./scan-report/README.md) |
| [`scan-issues`](./scan-issues/) | Create or update GitHub Issues from scan results | [README](./scan-issues/README.md) |

## Quick start

```yaml
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

      - name: Generate report
        id: report
        uses: cascadeguard/cascadeguard-actions/scan-report@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          grype-results: grype-results.json
          image: python-3.12-slim
          output-dir: reports/

      - name: Create CVE issues
        uses: cascadeguard/cascadeguard-actions/scan-issues@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67
        with:
          grype-results: grype-results.json
          image: python
          tag: 3.12-slim
          repo: ${{ github.repository }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

See the [cascadeguard-open-secure-images](https://github.com/cascadeguard/cascadeguard-open-secure-images) repository for real-world usage examples.

## Versioning

This repository uses SHA pinning for reproducibility.

```yaml
# Recommended — pinned SHA (use the latest SHA from the Actions tab)
uses: cascadeguard/cascadeguard-actions/setup-grype@da2a5b03ad98c2e99f9c2f9a162d1e9685aa7d67

# Or by tag after a tagged release
uses: cascadeguard/cascadeguard-actions/setup-grype@v1
```

After each tagged release, floating major-version tags (e.g. `v1`) are updated so you can opt in to automatic patch/minor updates.

## Contributing

Issues and PRs welcome. See the open [roadmap issues](https://github.com/cascadeguard/cascadeguard-actions/issues) for planned work.

## License

[MIT](LICENSE)