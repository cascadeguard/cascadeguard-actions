# Releasing cascadeguard-actions

This repo follows [GitHub Actions versioning conventions](https://github.com/actions/toolkit/blob/main/docs/action-versioning.md). Users reference actions by floating major tag (`@v1`) or pinned semver (`@v1.2.3`). For maximum security, pin by SHA.

## How to release

1. **Ensure `main` is green.** All CI checks must pass.

2. **Tag the release:**

   ```bash
   git checkout main
   git pull origin main
   git tag v1.0.0  # use the appropriate version
   git push origin v1.0.0
   ```

3. **The release workflow runs automatically:**
   - Validates the tag is valid semver (`vMAJOR.MINOR.PATCH`)
   - Creates a GitHub Release with auto-generated changelog
   - Force-updates the floating major-version tag (`v1`) to point to the new release

4. **Verify** the release at `https://github.com/cascadeguard/cascadeguard-actions/releases`.

## Version bumping

Follow [Semantic Versioning](https://semver.org/):

| Change type | Bump | Example |
|---|---|---|
| Breaking change to action inputs/outputs | Major | `v1.0.0` -> `v2.0.0` |
| New action or new optional input | Minor | `v1.0.0` -> `v1.1.0` |
| Bug fix, docs, internal refactor | Patch | `v1.0.0` -> `v1.0.1` |

## How users consume releases

```yaml
# Floating major (gets bug fixes automatically)
- uses: cascadeguard/cascadeguard-actions/scan-report@v1

# Pinned semver (predictable, explicit upgrades)
- uses: cascadeguard/cascadeguard-actions/scan-report@v1.2.3

# SHA-pinned (recommended for security — use `cascadeguard actions pin`)
- uses: cascadeguard/cascadeguard-actions/scan-report@abc123...  # v1.2.3
```

We recommend SHA pinning for production workflows. Use `cascadeguard actions pin` to automate this.
