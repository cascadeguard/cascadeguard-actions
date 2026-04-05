"""
Acceptance tests for the scan-issues composite action.

Tests the cascadeguard scan-issues CLI command which the action invokes:
  cascadeguard scan-issues --grype <file> --image <name> --repo <org/repo>

These tests mock the GitHub API — no real issue creation occurs.
GitHub API interactions are captured by MockGitHubAPI and asserted on.
"""

import pytest

from app import cmd_scan_issues
from .conftest import fixture, MockGitHubAPI


class _Args:
    """Minimal args namespace for cmd_scan_issues."""
    def __init__(self, grype=None, trivy=None, image="alpine", tag="stable", repo="org/repo"):
        self.grype = grype
        self.trivy = trivy
        self.image = image
        self.tag = tag
        self.repo = repo
        self.github_token = "fake-token"


class TestScanIssuesCreatesOneIssuePerCVE:
    """AC1: scan-issues creates one issue per CVE+package."""

    def test_creates_issue_for_each_critical_and_high(self):
        # grype-critical-high.json has 1 critical + 1 high + 1 medium
        # Only critical and high should produce issues
        args = _Args(grype=str(fixture("grype-critical-high.json")))

        with MockGitHubAPI() as gh:
            rc = cmd_scan_issues(args)

        assert rc == 0
        assert len(gh.created) == 2, f"Expected 2 issues (critical+high), got {len(gh.created)}"

    def test_issue_title_includes_cve_package_and_severity(self):
        args = _Args(grype=str(fixture("grype-critical-high.json")))

        with MockGitHubAPI() as gh:
            cmd_scan_issues(args)

        titles = [i["title"] for i in gh.created]
        assert any("CVE-2026-1001" in t and "libssl3" in t for t in titles), (
            f"Expected critical CVE issue in titles: {titles}"
        )
        assert any("CVE-2026-1002" in t and "curl" in t for t in titles), (
            f"Expected high CVE issue in titles: {titles}"
        )

    def test_issue_has_correct_labels(self):
        args = _Args(grype=str(fixture("grype-critical-high.json")), image="nginx")

        with MockGitHubAPI() as gh:
            cmd_scan_issues(args)

        for issue in gh.created:
            labels = issue.get("labels", [])
            assert "cve" in labels, f"Missing 'cve' label: {labels}"
            assert "automated" in labels, f"Missing 'automated' label: {labels}"
            assert any("severity:" in l for l in labels), f"Missing severity label: {labels}"
            assert any("image:nginx" == l for l in labels), f"Missing image label: {labels}"

    def test_medium_and_lower_do_not_create_issues(self):
        """CVEs below High severity must not create GitHub issues."""
        import json
        import tempfile, os

        grype_medium_only = {
            "matches": [{
                "vulnerability": {
                    "id": "CVE-2026-LOW",
                    "severity": "Medium",
                    "fix": {"versions": []},
                    "dataSource": "",
                },
                "artifact": {"name": "libfoo", "version": "1.0", "type": "deb"},
            }]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(grype_medium_only, f)
            tmp = f.name

        try:
            args = _Args(grype=tmp)
            with MockGitHubAPI() as gh:
                rc = cmd_scan_issues(args)
            assert rc == 0
            assert len(gh.created) == 0, "Medium CVEs should not create issues"
        finally:
            os.unlink(tmp)

    def test_no_input_returns_error(self):
        args = _Args()
        with MockGitHubAPI() as gh:
            rc = cmd_scan_issues(args)
        assert rc == 1


class TestScanIssuesDeduplicatesOnRerun:
    """AC2: scan-issues does not create a duplicate when issue already exists (open)."""

    def test_adds_comment_instead_of_creating_duplicate(self):
        existing_open = [{
            "number": 42,
            "state": "open",
            "title": "CVE-2026-1001: libssl3 (critical)",
            "labels": [{"name": "cve"}, {"name": "automated"}],
        }]
        args = _Args(grype=str(fixture("grype-critical-high.json")))

        with MockGitHubAPI(existing_open=existing_open) as gh:
            rc = cmd_scan_issues(args)

        assert rc == 0
        # Only the high CVE (curl) should be newly created; critical (libssl3) already open
        assert len(gh.created) == 1, f"Expected 1 new issue (high only), got {len(gh.created)}"
        assert len(gh.reopened) == 0, "Should not reopen an already-open issue"

        # A comment should be posted on the existing issue
        assert any(c["issue"] == 42 for c in gh.comments), (
            "Expected a re-detection comment on existing issue #42"
        )

    def test_redetection_comment_mentions_image_and_date(self):
        existing_open = [{
            "number": 55,
            "state": "open",
            "title": "CVE-2026-1001: libssl3 (critical)",
            "labels": [{"name": "cve"}],
        }]
        args = _Args(grype=str(fixture("grype-critical-high.json")), image="alpine", tag="3.19")

        with MockGitHubAPI(existing_open=existing_open) as gh:
            cmd_scan_issues(args)

        comment = next((c for c in gh.comments if c["issue"] == 55), None)
        assert comment is not None, "No comment posted on existing open issue"
        assert "alpine" in comment["body"], "Comment should mention the image name"


class TestScanIssuesReopensClosedIssues:
    """AC3: scan-issues reopens a closed issue when the CVE is re-detected."""

    def test_reopens_closed_issue(self):
        existing_closed = [{
            "number": 77,
            "state": "closed",
            "title": "CVE-2026-1001: libssl3 (critical)",
            "labels": [{"name": "cve"}, {"name": "automated"}],
        }]
        args = _Args(grype=str(fixture("grype-critical-high.json")))

        with MockGitHubAPI(existing_closed=existing_closed) as gh:
            rc = cmd_scan_issues(args)

        assert rc == 0
        assert 77 in gh.reopened, f"Issue #77 should have been reopened; reopened={gh.reopened}"

    def test_comment_posted_on_reopened_issue(self):
        existing_closed = [{
            "number": 88,
            "state": "closed",
            "title": "CVE-2026-1001: libssl3 (critical)",
            "labels": [{"name": "cve"}],
        }]
        args = _Args(grype=str(fixture("grype-critical-high.json")), image="nginx", tag="stable")

        with MockGitHubAPI(existing_closed=existing_closed) as gh:
            cmd_scan_issues(args)

        comment = next((c for c in gh.comments if c["issue"] == 88), None)
        assert comment is not None, "No comment posted on reopened issue"
        assert "nginx" in comment["body"], "Reopen comment should mention the image"

    def test_does_not_create_new_issue_when_closed_issue_exists(self):
        existing_closed = [{
            "number": 99,
            "state": "closed",
            "title": "CVE-2026-1001: libssl3 (critical)",
            "labels": [{"name": "cve"}],
        }]
        args = _Args(grype=str(fixture("grype-critical-high.json")))

        with MockGitHubAPI(existing_closed=existing_closed) as gh:
            cmd_scan_issues(args)

        # Should NOT have created a brand-new issue for the critical CVE
        created_titles = [i["title"] for i in gh.created]
        assert not any("CVE-2026-1001" in t for t in created_titles), (
            "Should reopen existing issue, not create a new one"
        )


class TestScanIssuesWithTrivyInput:
    """scan-issues also works with Trivy scanner output."""

    def test_trivy_high_creates_issues(self):
        args = _Args(trivy=str(fixture("trivy-high.json")))

        with MockGitHubAPI() as gh:
            rc = cmd_scan_issues(args)

        assert rc == 0
        # trivy-high.json has 1 HIGH (zlib1g) + 1 MEDIUM (libc6)
        assert len(gh.created) == 1, f"Expected 1 issue (high only), got {len(gh.created)}"

    def test_combined_grype_and_trivy_deduplicates(self):
        """When both scanners report the same CVE+package, only one issue is created."""
        import json, tempfile, os

        grype = {
            "matches": [{
                "vulnerability": {
                    "id": "CVE-2026-DUPE",
                    "severity": "Critical",
                    "fix": {"versions": []},
                    "dataSource": "",
                },
                "artifact": {"name": "libcommon", "version": "1.0", "type": "deb"},
            }]
        }
        trivy = {
            "Results": [{
                "Type": "debian",
                "Vulnerabilities": [{
                    "VulnerabilityID": "CVE-2026-DUPE",
                    "PkgName": "libcommon",
                    "InstalledVersion": "1.0",
                    "Severity": "CRITICAL",
                }],
            }]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as gf:
            json.dump(grype, gf)
            gpath = gf.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(trivy, tf)
            tpath = tf.name

        try:
            args = _Args(grype=gpath, trivy=tpath)
            with MockGitHubAPI() as gh:
                rc = cmd_scan_issues(args)
            assert rc == 0
            assert len(gh.created) == 1, (
                f"Expected 1 deduplicated issue, got {len(gh.created)}"
            )
        finally:
            os.unlink(gpath)
            os.unlink(tpath)
