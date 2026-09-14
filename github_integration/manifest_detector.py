"""
LicenseLens — Manifest & File Detector for GitHub Repositories.
Detects dependency manifests (Python, Node.js, Java, Go, Rust, etc.),
nested structures, READMEs, and LICENSE files from repository trees.
"""

import os
import re

# Manifest definitions: filename or pattern -> (ecosystem, parser_supported, priority)
# Lower priority number = higher precedence when multiple manifests for same ecosystem exist.
MANIFEST_DEFINITIONS = {
    'package.json': {
        'ecosystem': 'npm',
        'display_name': 'Node.js (package.json)',
        'supported': True,
        'parser': 'package.json',
        'priority': 1,
    },
    'package-lock.json': {
        'ecosystem': 'npm',
        'display_name': 'Node.js Lockfile (package-lock.json)',
        'supported': False,
        'parser': None,
        'priority': 2,
    },
    'yarn.lock': {
        'ecosystem': 'npm',
        'display_name': 'Yarn Lockfile (yarn.lock)',
        'supported': False,
        'parser': None,
        'priority': 3,
    },
    'pnpm-lock.yaml': {
        'ecosystem': 'npm',
        'display_name': 'pnpm Lockfile (pnpm-lock.yaml)',
        'supported': False,
        'parser': None,
        'priority': 4,
    },
    'requirements.txt': {
        'ecosystem': 'pypi',
        'display_name': 'Python (requirements.txt)',
        'supported': True,
        'parser': 'requirements.txt',
        'priority': 1,
    },
    'pyproject.toml': {
        'ecosystem': 'pypi',
        'display_name': 'Python (pyproject.toml)',
        'supported': False,
        'parser': None,
        'priority': 2,
    },
    'pipfile': {
        'ecosystem': 'pypi',
        'display_name': 'Python (Pipfile)',
        'supported': False,
        'parser': None,
        'priority': 3,
    },
    'pipfile.lock': {
        'ecosystem': 'pypi',
        'display_name': 'Python (Pipfile.lock)',
        'supported': False,
        'parser': None,
        'priority': 4,
    },
    'poetry.lock': {
        'ecosystem': 'pypi',
        'display_name': 'Poetry Lockfile (poetry.lock)',
        'supported': False,
        'parser': None,
        'priority': 5,
    },
    'pom.xml': {
        'ecosystem': 'maven',
        'display_name': 'Java Maven (pom.xml)',
        'supported': False,
        'parser': None,
        'priority': 1,
    },
    'build.gradle': {
        'ecosystem': 'gradle',
        'display_name': 'Gradle (build.gradle)',
        'supported': False,
        'parser': None,
        'priority': 2,
    },
    'build.gradle.kts': {
        'ecosystem': 'gradle',
        'display_name': 'Gradle Kotlin (build.gradle.kts)',
        'supported': False,
        'parser': None,
        'priority': 3,
    },
    'go.mod': {
        'ecosystem': 'golang',
        'display_name': 'Go (go.mod)',
        'supported': False,
        'parser': None,
        'priority': 1,
    },
    'cargo.toml': {
        'ecosystem': 'cargo',
        'display_name': 'Rust (Cargo.toml)',
        'supported': False,
        'parser': None,
        'priority': 1,
    },
    'composer.json': {
        'ecosystem': 'packagist',
        'display_name': 'PHP Composer (composer.json)',
        'supported': False,
        'parser': None,
        'priority': 1,
    },
    'gemfile': {
        'ecosystem': 'rubygems',
        'display_name': 'Ruby (Gemfile)',
        'supported': False,
        'parser': None,
        'priority': 1,
    },
}

README_NAMES = {'readme.md', 'readme', 'readme.txt', 'readme.rst', 'readme.markdown'}
LICENSE_NAMES = {'license', 'license.md', 'license.txt', 'licence', 'licence.md', 'licence.txt', 'copying', 'copying.txt'}

# Directories to ignore when traversing trees
IGNORED_DIRS = {
    'node_modules', 'vendor', '.git', '.github', 'venv', '.venv', 'env',
    '__pycache__', '.pytest_cache', '.tox', 'build', 'dist', 'target',
    '.next', '.nuxt', 'bin', 'obj'
}


class ManifestDetector:
    """
    Scans a repository tree (list of file paths or GitHub tree items)
    and classifies manifests, READMEs, and LICENSE files.
    """

    @classmethod
    def should_ignore_path(cls, path):
        parts = path.replace('\\', '/').split('/')
        for part in parts[:-1]:  # check directories leading up to filename
            if part.lower() in IGNORED_DIRS or part.startswith('.'):
                return True
        return False

    @classmethod
    def detect(cls, tree_items):
        """
        Analyze tree entries.
        tree_items can be a list of strings (paths) or list of dicts with 'path'.
        Returns structured detection result.
        """
        paths = []
        for item in tree_items:
            if isinstance(item, dict):
                # Skip submodules or git trees if marked
                if item.get('type') in ('tree', 'commit'):
                    continue
                p = item.get('path', '')
            else:
                p = str(item)
            if p:
                paths.append(p)

        detected_manifests = []
        readmes = []
        licenses = []

        for p in paths:
            if cls.should_ignore_path(p):
                continue

            normalized_path = p.replace('\\', '/')
            base_name = os.path.basename(normalized_path).lower()

            # Check README
            if base_name in README_NAMES:
                readmes.append({
                    'path': normalized_path,
                    'filename': os.path.basename(normalized_path),
                    'depth': normalized_path.count('/'),
                })

            # Check License
            if base_name in LICENSE_NAMES:
                licenses.append({
                    'path': normalized_path,
                    'filename': os.path.basename(normalized_path),
                    'depth': normalized_path.count('/'),
                })

            # Check exact match manifest
            if base_name in MANIFEST_DEFINITIONS:
                meta = MANIFEST_DEFINITIONS[base_name]
                detected_manifests.append({
                    'path': normalized_path,
                    'filename': os.path.basename(normalized_path),
                    'directory': os.path.dirname(normalized_path) or '.',
                    'ecosystem': meta['ecosystem'],
                    'display_name': meta['display_name'],
                    'supported': meta['supported'],
                    'parser': meta['parser'],
                    'priority': meta['priority'],
                    'depth': normalized_path.count('/'),
                })
            # Check pattern match (e.g. *.csproj)
            elif base_name.endswith('.csproj'):
                detected_manifests.append({
                    'path': normalized_path,
                    'filename': os.path.basename(normalized_path),
                    'directory': os.path.dirname(normalized_path) or '.',
                    'ecosystem': 'nuget',
                    'display_name': f'.NET Project ({os.path.basename(normalized_path)})',
                    'supported': False,
                    'parser': None,
                    'priority': 1,
                    'depth': normalized_path.count('/'),
                })

        # Sort readmes and licenses so root (depth 0) comes first
        readmes.sort(key=lambda r: (r['depth'], len(r['path'])))
        licenses.sort(key=lambda l: (l['depth'], len(l['path'])))

        primary_readme = readmes[0] if readmes else None
        primary_license = licenses[0] if licenses else None

        # Sort manifests: supported first, then depth (root first), then priority
        detected_manifests.sort(key=lambda m: (
            0 if m['supported'] else 1,
            m['depth'],
            m['priority']
        ))

        supported_manifests = [m for m in detected_manifests if m['supported']]
        unsupported_manifests = [m for m in detected_manifests if not m['supported']]

        return {
            'has_manifests': len(detected_manifests) > 0,
            'has_supported_manifests': len(supported_manifests) > 0,
            'manifests': detected_manifests,
            'supported_manifests': supported_manifests,
            'unsupported_manifests': unsupported_manifests,
            'readme': primary_readme,
            'readmes': readmes,
            'license': primary_license,
            'licenses': licenses,
            'stats': {
                'total_manifests': len(detected_manifests),
                'supported_count': len(supported_manifests),
                'unsupported_count': len(unsupported_manifests),
                'has_readme': primary_readme is not None,
                'has_license': primary_license is not None,
            }
        }
