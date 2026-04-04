"""
Shared test configuration and fixtures for cascadeguard-actions acceptance tests.

The tests call the cascadeguard CLI functions directly (not via subprocess) so that
GitHub API calls can be mocked cleanly using unittest.mock.

Sys-path setup: looks for the cascadeguard app in the workspace-standard location
(../cascadeguard/app relative to the repo root, on the CAS-81 branch). In CI the
package is installed via pip install, which takes precedence.
"""

import json
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Resolve cascadeguard app on sys.path (workspace dev mode)
# ---------------------------------------------------------------------------

_WORKSPACE_APP = Path(__file__).resolve().parents[2] / "cascadeguard" / "app"
if _WORKSPACE_APP.exists() and str(_WORKSPACE_APP) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_APP))


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fixture(name: str) -> Path:
    return FIXTURES_DIR / name


# ---------------------------------------------------------------------------
# Mock GitHub API helper
# ---------------------------------------------------------------------------

def _make_urlopen_response(data, status: int = 200):
    """Build a mock context-manager response for urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.status = status
    encoded = json.dumps(data).encode()
    mock_resp.read.return_value = encoded
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class MockGitHubAPI:
    """
    Context manager that patches urllib.request.urlopen to intercept all
    GitHub API calls made by cmd_scan_issues.

    Usage::

        with MockGitHubAPI(existing_open=[...], existing_closed=[...]) as gh:
            result = cmd_scan_issues(args)
        assert len(gh.created) == 2
    """

    def __init__(self, existing_open=None, existing_closed=None):
        self.existing_open: list = existing_open or []
        self.existing_closed: list = existing_closed or []
        self.created: list = []        # issues created (full dicts)
        self.reopened: list = []       # issue numbers reopened
        self.comments: list = []       # dicts with issue + body
        self.label_calls: list = []    # /labels requests recorded
        self._next_number = 200
        self._patcher = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self._patcher = patch("urllib.request.urlopen", side_effect=self._dispatch)
        self._patcher.start()
        return self

    def __exit__(self, *args):
        self._patcher.stop()

    # ------------------------------------------------------------------
    # Request dispatcher
    # ------------------------------------------------------------------

    def _dispatch(self, req):
        url: str = req.full_url
        method: str = req.get_method()
        body = json.loads(req.data) if req.data else None

        # GET issues list (open or closed)
        if method == "GET" and "/issues?" in url and "labels=cve" in url:
            if "state=open" in url:
                return _make_urlopen_response(self.existing_open)
            else:
                return _make_urlopen_response(self.existing_closed)

        # POST create issue
        if method == "POST" and url.endswith("/issues"):
            number = self._next_number
            self._next_number += 1
            issue = {**(body or {}), "number": number, "state": "open"}
            self.created.append(issue)
            return _make_urlopen_response(issue, 201)

        # PATCH update issue (reopen)
        if method == "PATCH" and "/issues/" in url:
            # Extract issue number from URL path
            parts = url.split("/issues/")
            number = int(parts[-1].split("?")[0])
            self.reopened.append(number)
            state = (body or {}).get("state", "open")
            return _make_urlopen_response({"number": number, "state": state})

        # POST comment on issue
        if method == "POST" and "/comments" in url:
            parts = url.split("/issues/")
            number = int(parts[-1].split("/")[0])
            self.comments.append({"issue": number, "body": (body or {}).get("body", "")})
            return _make_urlopen_response({"id": 1}, 201)

        # POST /labels (ensure-label)
        if method == "POST" and "/labels" in url:
            self.label_calls.append(url)
            return _make_urlopen_response({}, 200)

        # GET /labels/{name} (label existence check if any)
        if method == "GET" and "/labels/" in url:
            return _make_urlopen_response({"name": url.split("/labels/")[-1]})

        # Fallback
        return _make_urlopen_response({})
