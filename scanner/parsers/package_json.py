"""
package.json parser — extracts npm dependencies.

Handles:
- dependencies
- devDependencies
- peerDependencies
- optionalDependencies
"""
import json
import logging
import re

logger = logging.getLogger(__name__)


def parse(file_content: str) -> list[dict]:
    """
    Parse package.json content and return a list of dependency dicts.

    Returns:
        [
            {
                'name': str,
                'version_spec': str,   # e.g. "^4.18.2"
                'version': str,        # cleaned version e.g. "4.18.2"
                'ecosystem': 'npm',
                'is_direct': bool,
                'dependency_type': str  # 'direct', 'dev', 'peer', 'optional'
            },
            ...
        ]
    """
    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid package.json: {e}")
        raise ValueError(f"Invalid JSON in package.json: {e}")

    if not isinstance(data, dict):
        raise ValueError("package.json must be a JSON object.")

    deps = []
    seen = set()

    def extract_deps(dep_dict, dep_type, is_direct):
        if not isinstance(dep_dict, dict):
            return
        for name, version_spec in dep_dict.items():
            if name in seen:
                continue
            seen.add(name)
            version = _clean_version(str(version_spec))
            deps.append({
                'name': name,
                'version_spec': str(version_spec),
                'version': version,
                'ecosystem': 'npm',
                'is_direct': is_direct,
                'dependency_type': dep_type,
            })

    extract_deps(data.get('dependencies', {}), 'direct', True)
    extract_deps(data.get('devDependencies', {}), 'dev', True)
    extract_deps(data.get('peerDependencies', {}), 'direct', True)
    extract_deps(data.get('optionalDependencies', {}), 'direct', True)

    logger.info(f"package.json: parsed {len(deps)} dependencies")
    return deps


def _clean_version(version_spec: str) -> str:
    """
    Extract a clean version number from a version spec.

    Examples:
        "^4.18.2" → "4.18.2"
        "~2.0.1"  → "2.0.1"
        ">=1.0.0" → "1.0.0"
        "latest"  → "latest"
        "*"       → "*"
    """
    # Remove common prefix characters
    clean = re.sub(r'^[\^~>=<! ]+', '', version_spec.strip())
    # Handle range specs like "1.0.0 - 2.0.0" → take first
    if ' - ' in clean:
        clean = clean.split(' - ')[0].strip()
    # Handle "||" alternatives — take first
    if '||' in clean:
        clean = clean.split('||')[0].strip()
        clean = re.sub(r'^[\^~>=<! ]+', '', clean)
    # If still empty or just wildcard, return as-is
    if not clean or clean in ('*', 'x', 'latest'):
        return version_spec.strip()
    return clean
