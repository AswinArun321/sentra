"""
requirements.txt parser — extracts Python (PyPI) dependencies.

Handles:
- Simple: requests
- Pinned: requests==2.31.0
- Range: requests>=2.0.0
- Compatible: requests~=2.31.0
- Options: -r other.txt (skipped), --index-url (skipped)
- Comments: # ...
- Extras: requests[security]==2.31.0
"""
import re
import logging

logger = logging.getLogger(__name__)

# Regex for a valid requirement line
REQUIREMENT_RE = re.compile(
    r'^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)'  # package name
    r'(\[[\w,\s-]+\])?'                                # extras (optional)
    r'\s*([><=!~^,\s\d.*]+)?'                          # version spec (optional)
)


def parse(file_content: str) -> list[dict]:
    """
    Parse requirements.txt content and return a list of dependency dicts.

    Returns:
        [
            {
                'name': str,
                'version_spec': str,   # e.g. "==2.31.0"
                'version': str,        # cleaned e.g. "2.31.0"
                'ecosystem': 'PyPI',
                'is_direct': True,
                'dependency_type': 'direct'
            },
            ...
        ]
    """
    deps = []
    seen = set()

    for raw_line in file_content.splitlines():
        line = raw_line.strip()

        # Skip empty lines, comments, and option lines
        if not line or line.startswith('#') or line.startswith('-') or line.startswith('http'):
            continue

        # Remove inline comments
        if ' #' in line:
            line = line[:line.index(' #')].strip()

        match = REQUIREMENT_RE.match(line)
        if not match:
            logger.debug(f"Skipping unrecognized requirements line: {line!r}")
            continue

        name = match.group(1)
        version_spec_raw = (match.group(4) or '').strip()

        # Normalize name (PEP 503)
        normalized_name = re.sub(r'[-_.]+', '-', name).lower()

        if normalized_name in seen:
            continue
        seen.add(normalized_name)

        version = _extract_version(version_spec_raw)

        deps.append({
            'name': name,           # keep original casing
            'version_spec': version_spec_raw,
            'version': version,
            'ecosystem': 'PyPI',
            'is_direct': True,
            'dependency_type': 'direct',
        })

    logger.info(f"requirements.txt: parsed {len(deps)} dependencies")
    return deps


def _extract_version(version_spec: str) -> str:
    """
    Extract a single clean version from a version spec.

    Examples:
        "==2.31.0"   → "2.31.0"
        ">=2.0,<3.0" → "2.0"
        "~=2.31.0"   → "2.31.0"
        ""           → ""
    """
    if not version_spec:
        return ''

    # Try to find a pinned version first (==)
    pinned = re.search(r'==\s*([\d.]+)', version_spec)
    if pinned:
        return pinned.group(1)

    # Compatible release (~=)
    compatible = re.search(r'~=\s*([\d.]+)', version_spec)
    if compatible:
        return compatible.group(1)

    # Take first version number found in the spec
    first_version = re.search(r'([\d.]+)', version_spec)
    if first_version:
        return first_version.group(1)

    return version_spec.strip()
