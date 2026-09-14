# Package maintenance health analyzer
import logging
import requests
from datetime import date, datetime

logger = logging.getLogger(__name__)

def _classify(last_date: date, count: int) -> dict:
    if not last_date:
        return {'maintenance_status': 'UNKNOWN', 'last_release_date': None, 'release_count': 0}
    days = (date.today() - last_date).days
    if days >= 365 * 4: status = 'ABANDONED'
    elif days >= 365 * 2: status = 'STALE'
    elif days >= 365: status = 'LOW_ACTIVITY'
    else: status = 'ACTIVE'
    return {'maintenance_status': status, 'last_release_date': last_date, 'release_count': count}

def get_maintenance_status(name: str, version: str, ecosystem: str) -> dict:
    """Checks release dates on PyPI or npm to detect stale or abandoned libraries."""
    latest_date, count = None, 0
    try:
        if ecosystem == 'PyPI':
            res = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
            if res.ok:
                releases = res.json().get('releases', {})
                count = len(releases)
                for rel_files in releases.values():
                    for f in rel_files:
                        up_time = f.get('upload_time')
                        if up_time:
                            dt = datetime.fromisoformat(up_time.replace('Z', '+00:00')).date()
                            if not latest_date or dt > latest_date:
                                latest_date = dt
        elif ecosystem == 'npm':
            res = requests.get(f"https://registry.npmjs.org/{name}", timeout=10)
            if res.ok:
                times = res.json().get('time', {})
                count = max(0, len(times) - 2)
                for k, v in times.items():
                    if k not in ('created', 'modified'):
                        dt = datetime.fromisoformat(v.replace('Z', '+00:00')).date()
                        if not latest_date or dt > latest_date:
                            latest_date = dt
    except Exception as e:
        logger.warning(f"Maintenance check failed for {name}: {e}")

    return _classify(latest_date, count)
