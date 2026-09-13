"""
License Analyzer — retrieves and normalizes open-source licenses.

Sources:
- PyPI JSON API: https://pypi.org/pypi/{name}/json
- npm Registry: https://registry.npmjs.org/{name}
"""
import re
import logging
import requests

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10

# License normalization map
LICENSE_ALIASES = {
    # MIT variants
    'mit license': 'MIT',
    'mit licence': 'MIT',
    'the mit license': 'MIT',
    'mit/x11': 'MIT',

    # Apache variants
    'apache license 2.0': 'Apache-2.0',
    'apache 2.0': 'Apache-2.0',
    'apache software license 2.0': 'Apache-2.0',
    'apache2': 'Apache-2.0',
    'apache license, version 2.0': 'Apache-2.0',
    'asf': 'Apache-2.0',

    # BSD variants
    'bsd license': 'BSD-3-Clause',
    'bsd 2-clause': 'BSD-2-Clause',
    'bsd 3-clause': 'BSD-3-Clause',
    'new bsd': 'BSD-3-Clause',
    'simplified bsd': 'BSD-2-Clause',
    'revised bsd': 'BSD-3-Clause',

    # GPL
    'gpl': 'GPL-2.0',
    'gpl-2': 'GPL-2.0',
    'gpl-3': 'GPL-3.0',
    'gnu general public license v2': 'GPL-2.0',
    'gnu general public license v3': 'GPL-3.0',
    'gnu gpl v2': 'GPL-2.0',
    'gnu gpl v3': 'GPL-3.0',

    # LGPL
    'lgpl': 'LGPL-2.1',
    'lgpl-2': 'LGPL-2.0',
    'lgpl-2.1': 'LGPL-2.1',
    'lgpl-3': 'LGPL-3.0',
    'gnu lesser general public license': 'LGPL-2.1',

    # AGPL
    'agpl': 'AGPL-3.0',
    'agpl-3': 'AGPL-3.0',
    'gnu affero general public license': 'AGPL-3.0',

    # MPL
    'mozilla public license 2.0': 'MPL-2.0',
    'mpl': 'MPL-2.0',
    'mpl-2': 'MPL-2.0',

    # ISC
    'isc license': 'ISC',

    # Public domain
    'public domain': 'Public Domain',
    'unlicense': 'Unlicense',
    'cc0': 'CC0-1.0',
    'creative commons zero': 'CC0-1.0',

    # Unknown/proprietary
    'proprietary': 'Proprietary',
    'commercial': 'Proprietary',
    'see license': 'Unknown',
    'see license in license': 'Unknown',
}

# License category classification
LICENSE_CATEGORIES = {
    # Permissive
    'MIT': 'PERMISSIVE',
    'Apache-2.0': 'PERMISSIVE',
    'BSD-2-Clause': 'PERMISSIVE',
    'BSD-3-Clause': 'PERMISSIVE',
    'ISC': 'PERMISSIVE',
    'Unlicense': 'PERMISSIVE',
    'CC0-1.0': 'PERMISSIVE',
    'Public Domain': 'PERMISSIVE',
    'Artistic-2.0': 'PERMISSIVE',
    'Boost-1.0': 'PERMISSIVE',
    'zlib': 'PERMISSIVE',
    'PSF-2.0': 'PERMISSIVE',

    # Weak copyleft
    'LGPL-2.0': 'WEAK_COPYLEFT',
    'LGPL-2.1': 'WEAK_COPYLEFT',
    'LGPL-3.0': 'WEAK_COPYLEFT',
    'MPL-2.0': 'WEAK_COPYLEFT',
    'EPL-1.0': 'WEAK_COPYLEFT',
    'EPL-2.0': 'WEAK_COPYLEFT',
    'CDDL-1.0': 'WEAK_COPYLEFT',

    # Strong copyleft
    'GPL-2.0': 'STRONG_COPYLEFT',
    'GPL-3.0': 'STRONG_COPYLEFT',
    'AGPL-3.0': 'STRONG_COPYLEFT',

    # Proprietary
    'Proprietary': 'PROPRIETARY',
}


def get_license(name: str, version: str, ecosystem: str) -> dict:
    """
    Retrieve and normalize the license for a package.

    Returns:
        {
            'license': str,           # Normalized license name
            'license_category': str,  # PERMISSIVE / WEAK_COPYLEFT / STRONG_COPYLEFT / PROPRIETARY / UNKNOWN
            'license_source': str,    # 'pypi' or 'npm'
        }
    """
    if ecosystem == 'PyPI':
        return _get_pypi_license(name, version)
    elif ecosystem == 'npm':
        return _get_npm_license(name, version)
    return {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'none'}


def _get_pypi_license(name: str, version: str) -> dict:
    """Fetch license from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            return {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'pypi'}
        response.raise_for_status()
        data = response.json()
        info = data.get('info', {})

        # Try license field
        raw_license = info.get('license', '') or ''

        # Try classifiers if license field is empty
        if not raw_license or raw_license.lower() in ('unknown', ''):
            classifiers = info.get('classifiers', [])
            for c in classifiers:
                if c.startswith('License ::'):
                    parts = c.split(' :: ')
                    if len(parts) >= 3:
                        raw_license = parts[-1]
                        break

        normalized = normalize_license(raw_license)
        category = get_license_category(normalized)

        return {
            'license': normalized,
            'license_category': category,
            'license_source': 'pypi',
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"PyPI license fetch failed for {name}: {e}")
        return {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'pypi'}


def _get_npm_license(name: str, version: str) -> dict:
    """Fetch license from npm registry."""
    url = f"https://registry.npmjs.org/{name}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            return {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'npm'}
        response.raise_for_status()
        data = response.json()

        # Try latest version license first
        raw_license = ''
        dist_tags = data.get('dist-tags', {})
        latest = dist_tags.get('latest', '')
        if latest and latest in data.get('versions', {}):
            ver_data = data['versions'][latest]
            raw_license = _extract_npm_license(ver_data)

        # Fall back to top-level
        if not raw_license:
            raw_license = _extract_npm_license(data)

        normalized = normalize_license(raw_license)
        category = get_license_category(normalized)

        return {
            'license': normalized,
            'license_category': category,
            'license_source': 'npm',
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"npm license fetch failed for {name}: {e}")
        return {'license': 'Unknown', 'license_category': 'UNKNOWN', 'license_source': 'npm'}


def _extract_npm_license(data: dict) -> str:
    """Extract license string from npm package data."""
    license_field = data.get('license', '')
    if isinstance(license_field, dict):
        return license_field.get('type', '') or license_field.get('name', '')
    if isinstance(license_field, str):
        return license_field
    # Try 'licenses' array
    licenses = data.get('licenses', [])
    if licenses and isinstance(licenses, list):
        first = licenses[0]
        if isinstance(first, dict):
            return first.get('type', '')
        return str(first)
    return ''


def normalize_license(raw: str) -> str:
    """Normalize a raw license string to a standard SPDX-like identifier."""
    if not raw:
        return 'Unknown'

    # Clean up
    cleaned = raw.strip()

    # Handle SPDX expressions with OR/AND — take first
    if ' OR ' in cleaned.upper():
        cleaned = cleaned.split(' OR ')[0].strip().strip('(').strip(')')
    if ' AND ' in cleaned.upper():
        cleaned = cleaned.split(' AND ')[0].strip().strip('(').strip(')')

    # Check alias map (lowercase)
    lower = cleaned.lower()
    if lower in LICENSE_ALIASES:
        return LICENSE_ALIASES[lower]

    # Try to match known license identifiers
    known = [
        'MIT', 'Apache-2.0', 'Apache-1.0', 'BSD-2-Clause', 'BSD-3-Clause',
        'GPL-2.0', 'GPL-3.0', 'GPL-2.0-only', 'GPL-3.0-only',
        'LGPL-2.0', 'LGPL-2.1', 'LGPL-3.0',
        'AGPL-3.0', 'MPL-2.0', 'ISC', 'CC0-1.0',
        'Unlicense', 'PSF-2.0', 'EUPL-1.2',
        'EPL-1.0', 'EPL-2.0', 'CDDL-1.0',
    ]
    for lic in known:
        if lic.lower() in lower or lower == lic.lower():
            return lic

    # Return as-is if it looks like a license identifier (short, no spaces)
    if len(cleaned) <= 30 and ' ' not in cleaned:
        return cleaned

    # Return first 50 chars if very long
    return cleaned[:50] if cleaned else 'Unknown'


def get_license_category(license_name: str) -> str:
    """Return the category for a normalized license name."""
    if not license_name or license_name == 'Unknown':
        return 'UNKNOWN'

    # Direct lookup
    if license_name in LICENSE_CATEGORIES:
        return LICENSE_CATEGORIES[license_name]

    # Partial match
    upper = license_name.upper()
    if 'AGPL' in upper:
        return 'STRONG_COPYLEFT'
    if 'GPL' in upper:
        return 'STRONG_COPYLEFT'
    if 'LGPL' in upper or 'MPL' in upper or 'EPL' in upper:
        return 'WEAK_COPYLEFT'
    if 'MIT' in upper or 'APACHE' in upper or 'BSD' in upper or 'ISC' in upper:
        return 'PERMISSIVE'
    if 'PROPRIETARY' in upper or 'COMMERCIAL' in upper:
        return 'PROPRIETARY'

    return 'UNKNOWN'


def get_compliance_status(license_category: str) -> dict:
    """Return compliance status and explanation for a license category."""
    if license_category == 'PERMISSIVE':
        return {
            'status': 'COMPATIBLE',
            'label': 'Compatible',
            'color': 'success',
            'reason': 'Permissive licenses generally allow use in most projects without significant restrictions.',
        }
    elif license_category == 'WEAK_COPYLEFT':
        return {
            'status': 'REVIEW_REQUIRED',
            'label': 'Review Required',
            'color': 'warning',
            'reason': 'Weak copyleft licenses may require modifications to be shared under the same license. Review how this library is linked and distributed.',
        }
    elif license_category == 'STRONG_COPYLEFT':
        return {
            'status': 'POTENTIAL_CONFLICT',
            'label': 'Potential Conflict',
            'color': 'danger',
            'reason': 'Strong copyleft licenses (GPL/AGPL) may require your entire application to be released under the same license. Compatibility depends on how the software is combined and distributed.',
        }
    elif license_category == 'PROPRIETARY':
        return {
            'status': 'REVIEW_REQUIRED',
            'label': 'Proprietary',
            'color': 'danger',
            'reason': 'Proprietary or commercial licenses may have restrictions. Review the license terms carefully.',
        }
    else:
        return {
            'status': 'UNKNOWN',
            'label': 'Unknown',
            'color': 'secondary',
            'reason': 'License information is not available. Manual review is recommended.',
        }
