"""
Testable matrix generation logic for CI/CD workflows.

Provides functions to generate GitHub Actions matrix JSON from
parsed images.yaml data. Shared by build, scheduled-scan, and release
matrix generation jobs.
"""

from typing import List, Optional


def derive_image_path(dockerfile: str) -> str:
    """Extract the directory containing the Dockerfile.

    Example: "images/python/3.12/Dockerfile" -> "images/python/3.12"
             "local/seed/Dockerfile"          -> "local/seed"
    """
    parts = dockerfile.split("/")
    return "/".join(parts[:-1])


def _active_images(images_data: list[dict]) -> list[dict]:
    """Return only enabled image entries."""
    return [img for img in images_data if img.get("enabled", True) is not False]


def _resolve_dockerfile(img: dict) -> Optional[str]:
    """Resolve the dockerfile path from source.dockerfile or legacy root field.

    Returns None if no dockerfile is configured or build is disabled.
    """
    build_config = img.get("build", {})
    if isinstance(build_config, dict) and build_config.get("enabled") is False:
        return None
    source = img.get("source", {})
    if isinstance(source, dict):
        return source.get("dockerfile") or img.get("dockerfile")
    return img.get("dockerfile")


def generate_scan_matrix(
    images_data: list[dict],
    image_filter: str = "",
) -> list[dict]:
    """Generate CI/scan matrix entries.

    Each entry has: image_path, image_name, image_tag.
    Optionally filters to a single image by name.

    Args:
        images_data: Parsed images.yaml list.
        image_filter: If non-empty, include only images matching this name.

    Returns:
        List of dicts with keys ``image_path``, ``image_name``, ``image_tag``.
    """
    active = _active_images(images_data)
    include = []
    for img in active:
        if image_filter and img.get("image") != image_filter:
            continue
        include.append({
            "image_path": derive_image_path(img["dockerfile"]),
            "image_name": img["image"],
            "image_tag": img["tag"],
        })
    return include


def generate_scan_matrix_with_dir(images_data: list[dict]) -> list[dict]:
    """Generate scheduled-scan matrix entries with directory paths.

    Each entry has: name, tag, dir.
    The ``dir`` field is everything except the filename from the dockerfile
    path (e.g., ``images/python/3.12``).

    Args:
        images_data: Parsed images.yaml list.

    Returns:
        List of dicts with keys ``name``, ``tag``, ``dir``.
    """
    active = _active_images(images_data)
    return [
        {
            "name": img["image"],
            "tag": img["tag"],
            "dir": "/".join(img["dockerfile"].split("/")[:-1]),
        }
        for img in active
    ]


def generate_release_matrix(images_data: list[dict]) -> list[dict]:
    """Generate release matrix entries.

    Each entry has: context, name, tag.
    The ``context`` field is the directory containing the Dockerfile.

    Args:
        images_data: Parsed images.yaml list.

    Returns:
        List of dicts with keys ``context``, ``name``, ``tag``.
    """
    active = _active_images(images_data)
    return [
        {
            "context": "/".join(img["dockerfile"].split("/")[:-1]),
            "name": img["image"],
            "tag": img["tag"],
        }
        for img in active
    ]


def generate_build_matrix(
    images_data: list,
    image_filter: str = "",
    changed_files: Optional[List[str]] = None,
) -> dict:
    """Generate a build matrix, optionally filtered by changed files.

    When *changed_files* is provided, only images whose Dockerfile
    directory was touched are included — unless ``shared/``,
    ``images.yaml``, or ``.github/workflows/`` changed, in which case
    all images are rebuilt.

    Args:
        images_data: Parsed images.yaml list.
        image_filter: If non-empty, only include images matching this name.
        changed_files: List of changed file paths from the push.
            ``None`` or empty means rebuild all.

    Returns:
        ``{"include": [...], "has_images": True/False}``
    """
    changed = [f for f in (changed_files or []) if f.strip()]

    rebuild_all = (
        not changed
        or any(f.startswith("shared/") for f in changed)
        or any(f == "images.yaml" for f in changed)
        or any(f.startswith(".github/workflows/") for f in changed)
    )

    active = _active_images(images_data)
    include = []

    for img in active:
        dockerfile = _resolve_dockerfile(img)
        if not dockerfile:
            continue

        image_path = derive_image_path(dockerfile)
        image_dir = "/".join(dockerfile.split("/")[:-1])

        if image_filter and img.get("image") != image_filter:
            continue

        if not rebuild_all:
            if not any(f.startswith(image_dir + "/") for f in changed):
                continue

        include.append({
            "image_path": image_path,
            "image_name": img["image"],
            "image_tag": str(img["tag"]),
        })

    return {
        "include": include,
        "has_images": len(include) > 0,
    }
