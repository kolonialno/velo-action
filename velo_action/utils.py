from semantic_version import Version,SimpleSpec
from typing import List, Optional

def find_matching_version(versions: List[str], version_to_match: Optional[float]) -> Optional[str]:
    """
    Finds the highest matching version in a list of versions.
    using the python semantic_version package.
    """
    if version_to_match is None:
        return None

    versions = [Version.coerce(v) for v in versions]
    s = SimpleSpec(str(version_to_match))
    matching_version = s.select(versions)
    return str(matching_version)
    
