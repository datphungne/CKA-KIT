"""Load and validate days/dayXX/HINTS.yaml (progressive hints + reference solutions).

Schema per exercise id ("01.1" ... "20.5"):
    docs:      list of {title, url}; url must be on a site allowed during the CKA exam
    hint:      short nudge shown together with the docs
    solution:  shell commands, written for the lab terminal (day namespace is the default)
    automated: true when tests/test_solutions.py runs the solution and expects the grader to PASS
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
# Documentation the CKA Candidate Handbook allows during the exam.
EXAM_DOC_HOSTS = {'kubernetes.io', 'helm.sh', 'gateway-api.sigs.k8s.io'}


class HintError(ValueError):
    pass


def hints_path(day: int) -> Path:
    return ROOT / 'days' / f'day{day:02d}' / 'HINTS.yaml'


def _check_exercise(key: str, item: object) -> dict:
    if not isinstance(item, dict):
        raise HintError(f'{key}: expected a mapping')
    docs = item.get('docs') or []
    if not docs or not isinstance(docs, list):
        raise HintError(f'{key}: at least one docs link is required')
    clean_docs = []
    for doc in docs:
        url = str(doc.get('url', '')) if isinstance(doc, dict) else ''
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in EXAM_DOC_HOSTS:
            raise HintError(f'{key}: docs url not on an exam-allowed site: {url!r}')
        clean_docs.append({'title': str(doc.get('title') or url), 'url': url})
    for field in ('hint', 'solution'):
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise HintError(f'{key}: missing {field}')
    return {'docs': clean_docs, 'hint': item['hint'].strip(), 'solution': item['solution'].rstrip() + '\n',
            'automated': bool(item.get('automated', False))}


def load_hints(day: int) -> dict[str, dict]:
    path = hints_path(day)
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    exercises = data.get('exercises') if isinstance(data, dict) else None
    if not isinstance(exercises, dict):
        raise HintError(f'{path.name}: top-level "exercises" mapping missing')
    prefix = f'{day:02d}.'
    result = {}
    for key, item in exercises.items():
        key = str(key)
        if not key.startswith(prefix):
            raise HintError(f'{key}: does not belong to day {day:02d}')
        result[key] = _check_exercise(key, item)
    return result
