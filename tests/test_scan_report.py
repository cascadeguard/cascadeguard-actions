"""
Acceptance tests for the scan-report composite action.

Tests the cascadeguard scan-report CLI command which the action invokes:
  cascadeguard scan-report --grype <file> --image <name> --dir <output-dir>

These tests run without Grype/Trivy installed — fixture JSON files supply
scanner output.
"""

import json
import pytest
from pathlib import Path

from app import cmd_scan_report
from .conftest import fixture


class _Args:
    """Minimal args namespace for cmd_scan_report."""
    def __init__(self, grype=None, trivy=None, image="alpine", dir=None):
        self.grype = grype
        self.trivy = trivy
        self.image = image
        self.dir = dir


class TestScanReportGeneratesFiles:
    """AC4: scan-report generates vulnerability-report.json and .md."""

    def test_writes_json_and_md_from_grype(self, tmp_path):
        args = _Args(
            grype=str(fixture("grype-critical-high.json")),
            image="nginx",
            dir=str(tmp_path / "reports"),
        )
        rc = cmd_scan_report(args)

        assert rc == 0
        json_path = tmp_path / "reports" / "vulnerability-report.json"
        md_path = tmp_path / "reports" / "vulnerability-report.md"
        assert json_path.exists(), "JSON report not written"
        assert md_path.exists(), "Markdown report not written"

    def test_json_report_content(self, tmp_path):
        args = _Args(
            grype=str(fixture("grype-critical-high.json")),
            image="nginx",
            dir=str(tmp_path / "reports"),
        )
        cmd_scan_report(args)

        report = json.loads((tmp_path / "reports" / "vulnerability-report.json").read_text())
        assert report["image"] == "nginx"
        assert "scan_date" in report
        assert report["summary"]["critical"] == 1
        assert report["summary"]["high"] == 1
        assert report["summary"]["medium"] == 1
        assert report["summary"]["total"] == 3

    def test_json_findings_structure(self, tmp_path):
        args = _Args(
            grype=str(fixture("grype-critical-high.json")),
            image="alpine",
            dir=str(tmp_path / "reports"),
        )
        cmd_scan_report(args)

        report = json.loads((tmp_path / "reports" / "vulnerability-report.json").read_text())
        findings = report["findings"]
        assert len(findings) == 3

        critical = next(f for f in findings if f["cve"] == "CVE-2026-1001")
        assert critical["severity"] == "Critical"
        assert critical["package"] == "libssl3"
        assert critical["fix_versions"] == ["3.0.15"]

        high = next(f for f in findings if f["cve"] == "CVE-2026-1002")
        assert high["severity"] == "High"
        assert high["fix_versions"] == []

    def test_markdown_report_contains_cve_table(self, tmp_path):
        args = _Args(
            grype=str(fixture("grype-critical-high.json")),
            image="alpine",
            dir=str(tmp_path / "reports"),
        )
        cmd_scan_report(args)

        md = (tmp_path / "reports" / "vulnerability-report.md").read_text()
        assert "# Vulnerability Report: alpine" in md
        assert "CVE-2026-1001" in md
        assert "Critical" in md
        assert "CVE-2026-1002" in md

    def test_writes_json_and_md_from_trivy(self, tmp_path):
        args = _Args(
            trivy=str(fixture("trivy-high.json")),
            image="debian-slim",
            dir=str(tmp_path / "reports"),
        )
        rc = cmd_scan_report(args)

        assert rc == 0
        report = json.loads((tmp_path / "reports" / "vulnerability-report.json").read_text())
        assert report["summary"]["high"] == 1
        assert report["summary"]["medium"] == 1

    def test_deduplicates_when_both_scanners_report_same_cve(self, tmp_path):
        """When grype and trivy both find the same CVE+package, it appears once."""
        import json as _json
        grype = {
            "matches": [{
                "vulnerability": {
                    "id": "CVE-2026-9999",
                    "severity": "Critical",
                    "fix": {"versions": [{"version": "2.0"}]},
                    "dataSource": "",
                },
                "artifact": {"name": "libfoo", "version": "1.0", "type": "deb"},
            }]
        }
        trivy = {
            "Results": [{
                "Type": "debian",
                "Vulnerabilities": [{
                    "VulnerabilityID": "CVE-2026-9999",
                    "PkgName": "libfoo",
                    "InstalledVersion": "1.0",
                    "Severity": "CRITICAL",
                }],
            }]
        }
        g = tmp_path / "grype.json"
        t = tmp_path / "trivy.json"
        g.write_text(_json.dumps(grype))
        t.write_text(_json.dumps(trivy))

        args = _Args(grype=str(g), trivy=str(t), image="test", dir=str(tmp_path / "r"))
        cmd_scan_report(args)

        report = _json.loads((tmp_path / "r" / "vulnerability-report.json").read_text())
        assert report["summary"]["total"] == 1, "duplicate CVE+package should be deduplicated"

    def test_no_commit_when_content_unchanged(self, tmp_path):
        """Running scan-report twice with the same input produces identical files (idempotent)."""
        args = _Args(
            grype=str(fixture("grype-critical-high.json")),
            image="alpine",
            dir=str(tmp_path / "reports"),
        )
        cmd_scan_report(args)
        first_json = (tmp_path / "reports" / "vulnerability-report.json").read_text()
        first_md = (tmp_path / "reports" / "vulnerability-report.md").read_text()

        cmd_scan_report(args)
        second_json = (tmp_path / "reports" / "vulnerability-report.json").read_text()
        second_md = (tmp_path / "reports" / "vulnerability-report.md").read_text()

        # Content should be identical (same scan date and findings) so git
        # diff would show no changes and a commit would be skipped.
        assert first_json == second_json
        assert first_md == second_md

    def test_empty_scan_produces_no_findings(self, tmp_path):
        args = _Args(
            grype=str(fixture("grype-empty.json")),
            image="alpine",
            dir=str(tmp_path / "reports"),
        )
        rc = cmd_scan_report(args)

        assert rc == 0
        report = json.loads((tmp_path / "reports" / "vulnerability-report.json").read_text())
        assert report["summary"]["total"] == 0
        assert report["findings"] == []
        md = (tmp_path / "reports" / "vulnerability-report.md").read_text()
        assert "No vulnerabilities found" in md

    def test_no_input_returns_error(self, tmp_path):
        args = _Args(image="alpine", dir=str(tmp_path))
        rc = cmd_scan_report(args)
        assert rc == 1
