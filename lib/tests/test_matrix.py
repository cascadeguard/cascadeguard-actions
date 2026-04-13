"""Unit tests for lib/matrix.py — build matrix generation."""

import sys
from pathlib import Path

# Ensure lib/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matrix import generate_build_matrix, generate_scan_matrix


# ── Fixtures ───────────────────────────────────────────────────────────────

IMAGES = [
    {"name": "nginx", "image": "nginx", "tag": "stable-alpine-slim",
     "dockerfile": "images/nginx/Dockerfile"},
    {"name": "python", "image": "python", "tag": "3.12-slim",
     "dockerfile": "images/python/3.12/Dockerfile"},
    {"name": "alpine", "image": "alpine", "tag": "3.20",
     "dockerfile": "images/alpine/Dockerfile"},
    {"name": "memcached", "image": "memcached", "tag": "1.6",
     "enabled": False},
]


# ── generate_build_matrix ──────────────────────────────────────────────────


class TestBuildMatrixNoChangedFiles:
    """No changed_files → rebuild all enabled images."""

    def test_all_enabled_images_included(self):
        result = generate_build_matrix(IMAGES)
        assert result["has_images"] is True
        names = [e["image_name"] for e in result["include"]]
        assert "nginx" in names
        assert "python" in names
        assert "alpine" in names

    def test_disabled_images_excluded(self):
        result = generate_build_matrix(IMAGES)
        names = [e["image_name"] for e in result["include"]]
        assert "memcached" not in names

    def test_empty_changed_files_rebuilds_all(self):
        result = generate_build_matrix(IMAGES, changed_files=[])
        assert len(result["include"]) == 3

    def test_none_changed_files_rebuilds_all(self):
        result = generate_build_matrix(IMAGES, changed_files=None)
        assert len(result["include"]) == 3


class TestBuildMatrixChangedFiles:
    """Changed files filter the matrix to affected images only."""

    def test_only_changed_image_included(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["images/nginx/Dockerfile"])
        names = [e["image_name"] for e in result["include"]]
        assert names == ["nginx"]

    def test_nested_path_matches(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["images/python/3.12/some-script.sh"])
        names = [e["image_name"] for e in result["include"]]
        assert names == ["python"]

    def test_no_matching_changes_empty_matrix(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["README.md", "docs/guide.md"])
        assert result["has_images"] is False
        assert result["include"] == []

    def test_multiple_images_changed(self):
        result = generate_build_matrix(IMAGES,
            changed_files=[
                "images/nginx/Dockerfile",
                "images/alpine/hardening.sh",
            ])
        names = sorted(e["image_name"] for e in result["include"])
        assert names == ["alpine", "nginx"]


class TestBuildMatrixRebuildAllTriggers:
    """Changes to shared/, images.yaml, or workflows rebuild everything."""

    def test_shared_change_rebuilds_all(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["shared/hardening/strip-shells.sh"])
        assert len(result["include"]) == 3

    def test_images_yaml_change_rebuilds_all(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["images.yaml"])
        assert len(result["include"]) == 3

    def test_workflow_change_rebuilds_all(self):
        result = generate_build_matrix(IMAGES,
            changed_files=[".github/workflows/build.yaml"])
        assert len(result["include"]) == 3

    def test_mixed_trigger_and_image_rebuilds_all(self):
        result = generate_build_matrix(IMAGES,
            changed_files=["shared/scanning/grype.yaml", "images/nginx/Dockerfile"])
        assert len(result["include"]) == 3


class TestBuildMatrixImageFilter:
    """image_filter limits to a single named image."""

    def test_filter_single_image(self):
        result = generate_build_matrix(IMAGES, image_filter="python")
        names = [e["image_name"] for e in result["include"]]
        assert names == ["python"]

    def test_filter_with_changed_files(self):
        result = generate_build_matrix(IMAGES,
            image_filter="nginx",
            changed_files=["images/nginx/Dockerfile"])
        names = [e["image_name"] for e in result["include"]]
        assert names == ["nginx"]

    def test_filter_no_match(self):
        result = generate_build_matrix(IMAGES, image_filter="nonexistent")
        assert result["has_images"] is False

    def test_filter_disabled_image(self):
        result = generate_build_matrix(IMAGES, image_filter="memcached")
        assert result["has_images"] is False


class TestBuildMatrixOutputShape:
    """Matrix entries have the correct keys and types."""

    def test_entry_keys(self):
        result = generate_build_matrix(IMAGES)
        for entry in result["include"]:
            assert "image_path" in entry
            assert "image_name" in entry
            assert "image_tag" in entry

    def test_image_path_derived_correctly(self):
        result = generate_build_matrix(IMAGES)
        by_name = {e["image_name"]: e for e in result["include"]}
        assert by_name["nginx"]["image_path"] == "nginx"
        assert by_name["python"]["image_path"] == "python/3.12"
        assert by_name["alpine"]["image_path"] == "alpine"

    def test_tag_is_string(self):
        images = [{"name": "x", "image": "x", "tag": 3.20,
                    "dockerfile": "images/x/Dockerfile"}]
        result = generate_build_matrix(images)
        assert result["include"][0]["image_tag"] == "3.2"

    def test_no_dockerfile_skipped(self):
        images = [{"name": "x", "image": "x", "tag": "latest"}]
        result = generate_build_matrix(images)
        assert result["has_images"] is False
