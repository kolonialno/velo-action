from typing import List, Optional

from semantic_version import SimpleSpec, Version


def find_matching_version(
    versions: List[str], version_to_match: Optional[float]
) -> Optional[str]:
    """
    Finds the highest matching version in a list of versions.
    using the python semantic_version package.
    """
    if version_to_match is None:
        return None

    versions = [Version.coerce(v) for v in versions]
    parsed_versions = SimpleSpec(str(version_to_match))
    matching_version = parsed_versions.select(versions)
    return str(matching_version)
