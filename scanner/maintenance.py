"""
Maintenance Analyzer — checks package health and activity status.

Sources:
- PyPI JSON API: last release date, release frequency
- npm Registry: last publish date, version count
"""
import logging
import requests
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10

# Thresholds for maintenance classification
STALE_DAYS = 365 * 2        # 2 years without release = STALE
ABANDONED_DAYS = 365 * 4    # 4 years without release = ABANDONED
LOW_ACTIVITY_DAYS = 365     # 1 year without release = LOW_ACTIVITY


def get_maintenance_status(name: str, version: str, ecosystem: str) -> dict:
    """
    Determine maintenance status of a package.

    Returns:
        {
            'maintenance_status': str,   # ACTIVE / LOW_ACTIVITY / STALE / ABANDONED / UNKNOWN
            'last_release_date': date|None,
            'release_count': int,
            'days_since_release': int|None,
        }
    """
    if ecosystem == 'PyPI':
        return _check_pypi(name)
    elif ecosystem == 'npm':
        return _check_npm(name)
    return _unknown_result()


def _check_pypi(name: str) -> dict:
    """Check maintenance via PyPI JSON API."""
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            return _unknown_result()
        response.raise_for_status()
        data = response.json()

        releases = data.get('releases', {})
        release_count = len(releases)

        # Find the most recent release date
        latest_date = None
        for release_files in releases.values():
            for file_info in release_files:
                upload_time_str = file_info.get('upload_time', '')
                if upload_time_str:
                    try:
                        dt = datetime.fromisoformat(upload_time_str.replace('Z', '+00:00'))
                        release_date = dt.date()
                        if latest_date is None or release_date > latest_date:
                            latest_date = release_date
                    except ValueError:
                        pass

        return _classify(latest_date, release_count)

    except requests.exceptions.RequestException as e:
        logger.warning(f"PyPI maintenance check failed for {name}: {e}")
        return _unknown_result()


def _check_npm(name: str) -> dict:
    """Check maintenance via npm Registry."""
    # Use abbreviated registry response for speed
    url = f"https://registry.npmjs.org/{name}"
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'Accept': 'application/vnd.npm.install-v1+json'},
        )
        if response.status_code == 404:
            return _unknown_result()
        response.raise_for_status()
        data = response.json()

        # Time data
        time_data = data.get('time', {})
        release_count = max(0, len(time_data) - 2)  # subtract 'created' and 'modified'

        # Latest release date from 'modified' or latest version time
        latest_date = None
        dist_tags = data.get('dist-tags', {})
        latest_version = dist_tags.get('latest', '')

        if latest_version and latest_version in time_data:
            ts = time_data[latest_version]
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                latest_date = dt.date()
            except ValueError:
                pass

        # Fall back to 'modified'
        if not latest_date and 'modified' in time_data:
            try:
                dt = datetime.fromisoformat(time_data['modified'].replace('Z', '+00:00'))
                latest_date = dt.date()
            except ValueError:
                pass

        return _classify(latest_date, release_count)

    except requests.exceptions.RequestException as e:
        logger.warning(f"npm maintenance check failed for {name}: {e}")
        return _unknown_result()


def _classify(last_release_date: date | None, release_count: int) -> dict:
    """Classify maintenance status based on last release date."""
    if last_release_date is None:
        return _unknown_result()

    today = date.today()
    days_since = (today - last_release_date).days

    if days_since >= ABANDONED_DAYS:
        status = 'ABANDONED'
    elif days_since >= STALE_DAYS:
        status = 'STALE'
    elif days_since >= LOW_ACTIVITY_DAYS:
        status = 'LOW_ACTIVITY'
    else:
        status = 'ACTIVE'

    return {
        'maintenance_status': status,
        'last_release_date': last_release_date,
        'release_count': release_count,
        'days_since_release': days_since,
    }


def _unknown_result() -> dict:
    return {
        'maintenance_status': 'UNKNOWN',
        'last_release_date': None,
        'release_count': 0,
        'days_since_release': None,
    }
