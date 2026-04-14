"""
Testable resolve-image logic.

Looks up an image name in parsed images.yaml data and returns
the resolved path, name, tag, and whether it was found.
"""


def derive_image_path(dockerfile: str) -> str:
    """Extract the directory containing the Dockerfile.

    Example: "images/python/3.12/Dockerfile" -> "images/python/3.12"
             "local/seed/Dockerfile"          -> "local/seed"
    """
    parts = dockerfile.split("/")
    return "/".join(parts[:-1])


def resolve_image(
    images_data: list[dict],
    image_name: str,
    image_tag_override: str = "",
) -> dict:
    """Resolve an image name against parsed images.yaml data.

    Args:
        images_data: List of image entries from images.yaml.
        image_name: The image name to look up (matches the ``image`` field).
        image_tag_override: If non-empty, overrides the tag from images.yaml.

    Returns:
        A dict with keys ``image_path``, ``image_name``, ``image_tag``, ``found``.
    """
    for img in images_data:
        if not img.get("enabled", True):
            continue
        if img.get("image") == image_name:
            source = img.get("source", {})
            dockerfile = source.get("dockerfile") or img.get("dockerfile") if isinstance(source, dict) else img.get("dockerfile")
            if not dockerfile:
                continue
            image_path = derive_image_path(dockerfile)
            tag = image_tag_override if image_tag_override else img["tag"]
            return {
                "image_path": image_path,
                "image_name": image_name,
                "image_tag": tag,
                "found": True,
            }

    return {
        "image_path": "",
        "image_name": image_name,
        "image_tag": "",
        "found": False,
    }
