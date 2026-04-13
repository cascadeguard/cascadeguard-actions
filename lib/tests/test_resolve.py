"""Unit tests for lib/resolve.py — image resolution."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from resolve import resolve_image, derive_image_path


IMAGES = [
    {"name": "nginx", "image": "nginx", "tag": "stable-alpine-slim",
     "dockerfile": "images/nginx/Dockerfile"},
    {"name": "python", "image": "python", "tag": "3.12-slim",
     "dockerfile": "images/python/3.12/Dockerfile"},
    {"name": "disabled", "image": "disabled", "tag": "latest",
     "dockerfile": "images/disabled/Dockerfile", "enabled": False},
]


class TestDeriveImagePath:
    def test_simple(self):
        assert derive_image_path("images/nginx/Dockerfile") == "nginx"

    def test_nested(self):
        assert derive_image_path("images/python/3.12/Dockerfile") == "python/3.12"

    def test_deep(self):
        assert derive_image_path("images/a/b/c/Dockerfile") == "a/b/c"


class TestResolveImage:
    def test_found(self):
        result = resolve_image(IMAGES, "nginx")
        assert result["found"] is True
        assert result["image_path"] == "nginx"
        assert result["image_tag"] == "stable-alpine-slim"

    def test_tag_override(self):
        result = resolve_image(IMAGES, "nginx", "1.27")
        assert result["image_tag"] == "1.27"

    def test_not_found(self):
        result = resolve_image(IMAGES, "nonexistent")
        assert result["found"] is False

    def test_disabled_skipped(self):
        result = resolve_image(IMAGES, "disabled")
        assert result["found"] is False

    def test_nested_path(self):
        result = resolve_image(IMAGES, "python")
        assert result["image_path"] == "python/3.12"
