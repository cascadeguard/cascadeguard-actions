"""
Testable matrix generation logic for CI/CD workflows.

Provides functions to generate GitHub Actions matrix JSON from
parsed images.yaml data. Shared by scheduled-scan and release
matrix generation jobs.
"""


def derive_image_path(dockerfile: str) -> str:
    """Extract the path between the first and last segments.

    Example: "images/python/3.12/Dockerfile" -> "python/3.12"
    """
    parts = dockerfile.split("/")
    return "/".join(parts[1:-1])


def _active_images(images_data: list[dict]) -> list[dict]:
    """Return only enabled image entries."""
    return [img for img in images_data if img.get("enabled", True) is not False]


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
