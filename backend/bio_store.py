import os
import json
from typing import Dict, Any, List

USERS_BIO_FILE = os.getenv('USERS_BIO_FILE', 'users_bio.json')


def _read_all() -> Dict[str, Any]:
    try:
        if not os.path.exists(USERS_BIO_FILE):
            # Initialize file with an empty JSON object
            try:
                with open(USERS_BIO_FILE, 'w', encoding='utf-8') as f:
                    f.write('{}')
            except Exception:
                pass
            return {}
        with open(USERS_BIO_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_all(data: Dict[str, Any]) -> None:
    with open(USERS_BIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_record(username: str) -> Dict[str, Any]:
    users = _read_all()
    return users.get((username or '').lower(), {}) if isinstance(users, dict) else {}


def update_user_record(username: str, updates: Dict[str, Any]) -> None:
    users = _read_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    users[key].update(updates or {})
    _write_all(users)


def get_bio(username: str) -> str:
    rec = get_user_record(username)
    return str(rec.get('bio') or '')


def set_bio(username: str, bio: str) -> None:
    update_user_record(username, {'bio': str(bio or '')})


def get_personal_pool(username: str) -> List[Dict[str, Any]]:
    rec = get_user_record(username)
    pool = rec.get('personal_pool')
    return pool if isinstance(pool, list) else []


def set_personal_pool(username: str, pool: List[Dict[str, Any]]) -> None:
    if not isinstance(pool, list):
        pool = []
    update_user_record(username, {'personal_pool': pool})


