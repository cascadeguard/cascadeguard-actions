# cascadeguard-actions

Reusable composite GitHub Actions for CascadeGuard security workflows.

Pin these actions by SHA for reproducible, auditable CI pipelines.

## Actions

### `scan-report`

Parse Grype and/or Trivy scan results into a diffable vulnerability report.

```yaml
- uses: cascadeguard/cascadeguard-actions/scan-report@<sha>
  with:
    grype-results: grype-results.json
    trivy-results: trivy-results.json
    image: alpine
    output-dir: images/alpine/reports
```

**Inputs:**

| Input | Required | Description |
|---|---|---|
| `grype-results` | No* | Path to Grype JSON results |
| `trivy-results` | No* | Path to Trivy JSON results |
| `image` | Yes | Image name for metadata |
| `output-dir` | Yes | Where to write reports |
| `cascadeguard-version` | No | CLI git ref (default: `main`) |

\* At least one of `grype-results` or `trivy-results` must be provided.

**Outputs:** `report-json`, `report-md`, `total-cves`, `critical-count`, `high-count`

### `scan-issues`

Create or update GitHub issues from scan results. Opens new issues for Critical/High CVEs, re-detects existing ones, and reopens closed issues when a CVE reappears.

```yaml
- uses: cascadeguard/cascadeguard-actions/scan-issues@<sha>
  with:
    grype-results: grype-results.json
    trivy-results: trivy-results.json
    image: alpine
    tag: '3.20'
    repo: cascadeguard/cascadeguard-open-secure-images
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

**Inputs:**

| Input | Required | Description |
|---|---|---|
| `grype-results` | No* | Path to Grype JSON results |
| `trivy-results` | No* | Path to Trivy JSON results |
| `image` | Yes | Image name |
| `tag` | No | Image tag that was scanned |
| `repo` | Yes | GitHub repo for issue management |
| `github-token` | Yes | Token with issue write access |
| `cascadeguard-version` | No | CLI git ref (default: `main`) |

\* At least one of `grype-results` or `trivy-results` must be provided.

**Outputs:** `created`, `updated`, `reopened`

## Versioning

This repo uses SHA-pinned references. After each release:

1. Tag the release (e.g. `v0.1.0`)
2. Reference by full SHA in consuming workflows for maximum reproducibility

```yaml
# Pinned to exact commit SHA (recommended)
- uses: cascadeguard/cascadeguard-actions/scan-report@abc123def456

# Or by tag (less strict)
- uses: cascadeguard/cascadeguard-actions/scan-report@v0.1.0
```

## License

[MIT](LICENSE)
