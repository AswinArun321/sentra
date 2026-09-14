import re
import requests
import logging

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10

CATEGORIES = {
    'MIT': 'PERMISSIVE', 'Apache-2.0': 'PERMISSIVE', 'BSD-2-Clause': 'PERMISSIVE',
    'BSD-3-Clause': 'PERMISSIVE', 'ISC': 'PERMISSIVE', 'Unlicense': 'PERMISSIVE',
    'CC0-1.0': 'PERMISSIVE', 'Public Domain': 'PERMISSIVE', 'LGPL-2.1': 'WEAK_COPYLEFT',
    'LGPL-3.0': 'WEAK_COPYLEFT', 'MPL-2.0': 'WEAK_COPYLEFT', 'GPL-2.0': 'STRONG_COPYLEFT',
    'GPL-3.0': 'STRONG_COPYLEFT', 'AGPL-3.0': 'STRONG_COPYLEFT', 'Proprietary': 'PROPRIETARY'
}

def normalize_license(raw: str) -> str:
    """Normalize raw license name to a standard SPDX-compatible identifier."""
    if not raw:
        return 'Unknown'
    val = raw.split(' OR ')[0].split(' AND ')[0].strip('() ')
    s = val.lower()
    if 'mit' in s: return 'MIT'
    if 'apache' in s: return 'Apache-2.0'
    if 'bsd' in s: return 'BSD-3-Clause' if '3' in s else 'BSD-2-Clause'
    if 'agpl' in s: return 'AGPL-3.0'
    if 'lgpl' in s: return 'LGPL-3.0' if '3' in s else 'LGPL-2.1'
    if 'gpl' in s: return 'GPL-3.0' if '3' in s else 'GPL-2.0'
    if 'mpl' in s: return 'MPL-2.0'
    if 'isc' in s: return 'ISC'
    if 'unlicense' in s or 'cc0' in s: return 'Unlicense'
    if 'proprietary' in s or 'commercial' in s: return 'Proprietary'
    return val if val in CATEGORIES else 'Unknown'

def get_license_category(lic: str) -> str:
    return CATEGORIES.get(lic, 'UNKNOWN')

def get_license(name: str, version: str, ecosystem: str) -> dict:
    """Fetch package license from PyPI or npm."""
    raw_lic, source = '', 'none'
    try:
        if ecosystem == 'PyPI':
            source = 'pypi'
            res = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=REQUEST_TIMEOUT)
            if res.ok:
                info = res.json().get('info', {})
                raw_lic = info.get('license', '')
                if not raw_lic or raw_lic.lower() == 'unknown':
                    for c in info.get('classifiers', []):
                        if c.startswith('License ::'):
                            raw_lic = c.split(' :: ')[-1]
                            break
        elif ecosystem == 'npm':
            source = 'npm'
            res = requests.get(f"https://registry.npmjs.org/{name}", timeout=REQUEST_TIMEOUT)
            if res.ok:
                data = res.json()
                lic_data = data.get('license') or data.get('licenses', [{}])
                if isinstance(lic_data, list) and lic_data:
                    lic_data = lic_data[0]
                raw_lic = lic_data.get('type', '') if isinstance(lic_data, dict) else str(lic_data)
    except Exception as e:
        logger.warning(f"Failed fetching license for {name}: {e}")

    normalized = normalize_license(raw_lic)
    return {
        'license': normalized,
        'license_category': get_license_category(normalized),
        'license_source': source
    }
