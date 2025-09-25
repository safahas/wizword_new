import os
import json
import uuid
from typing import Dict, Any, List, Optional

USERS_BIO_FILE = os.getenv('USERS_BIO_FILE', 'users_bio.json')
USERS_FLASH_FILE = os.getenv('USERS_FLASH_FILE', 'users.flashcards.json')
FLASHCARD_MAX_SETS = int(os.getenv('FLASHCARD_MAX_SETS', '3') or '3')


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


# --- Separate FlashCard store ---
def _read_flash_all() -> Dict[str, Any]:
    try:
        if not os.path.exists(USERS_FLASH_FILE):
            try:
                with open(USERS_FLASH_FILE, 'w', encoding='utf-8') as f:
                    f.write('{}')
            except Exception:
                pass
            return {}
        with open(USERS_FLASH_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_flash_all(data: Dict[str, Any]) -> None:
    with open(USERS_FLASH_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_flash_user_record(username: str) -> Dict[str, Any]:
    users = _read_flash_all()
    return users.get((username or '').lower(), {}) if isinstance(users, dict) else {}


def _update_flash_user_record(username: str, updates: Dict[str, Any]) -> None:
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    users[key].update(updates or {})
    _write_flash_all(users)


def _maybe_migrate_flash_from_bio(username: str) -> None:
    """If flashcard data exists in users_bio.json but not in flash store, migrate it."""
    uname = (username or '').lower()
    flash_users = _read_flash_all()
    if isinstance(flash_users.get(uname), dict) and flash_users.get(uname):
        return  # already present
    # Look for legacy in bio
    rec = get_user_record(uname)
    if not isinstance(rec, dict):
        return
    legacy_sets = rec.get('flash_sets')
    legacy_active = rec.get('flash_active_set')
    legacy_text = rec.get('flash_text')
    legacy_pool = rec.get('flash_pool')
    migrated: Dict[str, Any] = {}
    if isinstance(legacy_sets, dict) and legacy_sets:
        migrated['flash_sets'] = legacy_sets
        if legacy_active:
            migrated['flash_active_set'] = legacy_active
        else:
            try:
                migrated['flash_active_set'] = next(iter(legacy_sets.keys()))
            except Exception:
                migrated['flash_active_set'] = 'default'
    elif legacy_text or legacy_pool:
        migrated['flash_sets'] = {
            'default': {
                'text': str(legacy_text or ''),
                'pool': legacy_pool if isinstance(legacy_pool, list) else [],
                'token': uuid.uuid4().hex[:8]
            }
        }
        migrated['flash_active_set'] = 'default'
    if migrated:
        _update_flash_user_record(uname, migrated)


def get_bio(username: str) -> str:
    rec = get_user_record(username)
    bio = str(rec.get('bio') or '')
    if bio:
        return bio
    # Fallback: attempt to import from users.json once if missing
    try:
        users_file = os.getenv('USERS_FILE', 'users.json')
        if os.path.exists(users_file):
            import json as _json
            with open(users_file, 'r', encoding='utf-8') as f:
                users = _json.load(f)
            key = (username or '').lower()
            if isinstance(users, dict) and key in users and isinstance(users[key], dict):
                legacy_bio = users[key].get('bio')
                if legacy_bio:
                    set_bio(username, legacy_bio)
                    return str(legacy_bio)
    except Exception:
        pass
    return ''


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


# --- FlashCard support (text + pool) ---
def get_flash_text(username: str) -> str:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    active = rec.get('flash_active_set')
    if isinstance(sets, dict) and active and active in sets:
        return str((sets.get(active) or {}).get('text') or '')
    return ''


def set_flash_text(username: str, text: str) -> None:
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    if 'flash_sets' not in rec or not isinstance(rec['flash_sets'], dict):
        rec['flash_sets'] = {}
    if not rec.get('flash_active_set'):
        rec['flash_active_set'] = 'default'
    active = rec['flash_active_set']
    if active not in rec['flash_sets'] and len(rec['flash_sets']) >= FLASHCARD_MAX_SETS:
        # Cannot create new set due to limit; ignore write
        pass
    else:
        if active not in rec['flash_sets']:
            rec['flash_sets'][active] = {'text': '', 'pool': []}
        rec['flash_sets'][active]['text'] = str(text or '')
    _write_flash_all(users)


def get_flash_pool(username: str) -> List[Dict[str, Any]]:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    active = rec.get('flash_active_set')
    if isinstance(sets, dict) and active and active in sets:
        item = (sets.get(active) or {})
        ref_tok = item.get('ref_token')
        if isinstance(ref_tok, str) and ref_tok:
            try:
                from backend.flash_share import load_share
                shared = load_share(ref_tok)
                if isinstance(shared, dict):
                    pool = shared.get('pool')
                    return pool if isinstance(pool, list) else []
            except Exception:
                return []
        pool = item.get('pool')
    return pool if isinstance(pool, list) else []
    return []


def set_flash_pool(username: str, pool: List[Dict[str, Any]]) -> None:
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    if 'flash_sets' not in rec or not isinstance(rec['flash_sets'], dict):
        rec['flash_sets'] = {}
    if not rec.get('flash_active_set'):
        rec['flash_active_set'] = 'default'
    active = rec['flash_active_set']
    # Do not overwrite a referenced set's pool
    try:
        cur = rec['flash_sets'].get(active) or {}
        if isinstance(cur.get('ref_token'), str) and cur.get('ref_token'):
            _write_flash_all(users)
            return
    except Exception:
        pass
    if active not in rec['flash_sets'] and len(rec['flash_sets']) >= FLASHCARD_MAX_SETS:
        # Cannot create new set due to limit; ignore write
        pass
    else:
        if active not in rec['flash_sets']:
            rec['flash_sets'][active] = {'text': '', 'pool': []}
        rec['flash_sets'][active]['pool'] = pool if isinstance(pool, list) else []
    _write_flash_all(users)


# --- FlashCard multi-set management ---
def list_flash_set_names(username: str) -> List[str]:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    return list(sets.keys()) if isinstance(sets, dict) else []


def get_active_flash_set_name(username: str) -> str:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    name = rec.get('flash_active_set')
    if name:
        return str(name)
    # Otherwise, first named set if exists
    names = list_flash_set_names(username)
    return names[0] if names else ''


def set_active_flash_set_name(username: str, name: str) -> None:
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    rec['flash_active_set'] = str(name or '')
    _write_flash_all(users)


def get_flash_set_text(username: str, name: str) -> str:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    item = (sets.get(name) or {}) if isinstance(sets, dict) else {}
    return str(item.get('text') or '')


def get_flash_set_pool(username: str, name: str) -> List[Dict[str, Any]]:
    _maybe_migrate_flash_from_bio(username)
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    item = (sets.get(name) or {}) if isinstance(sets, dict) else {}
    pool = item.get('pool')
    return pool if isinstance(pool, list) else []


def upsert_flash_set(username: str, name: str, text: str = '', pool: List[Dict[str, Any]] | None = None) -> bool:
    """Create or update a named flashcard set for user. Enforces FLASHCARD_MAX_SETS for new names.

    Returns True on success, False if refused due to limit or invalid name.
    """
    if not name:
        return False
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    if 'flash_sets' not in rec or not isinstance(rec['flash_sets'], dict):
        rec['flash_sets'] = {}
    is_new = name not in rec['flash_sets']
    if is_new and len(rec['flash_sets']) >= FLASHCARD_MAX_SETS:
        return False
    if is_new:
        rec['flash_sets'][name] = {
            'text': str(text or ''),
            'pool': list(pool or []),
            'token': uuid.uuid4().hex[:8]
        }
    else:
        if text is not None:
            rec['flash_sets'][name]['text'] = str(text or '')
        if pool is not None:
            rec['flash_sets'][name]['pool'] = list(pool)
        # If set exists but has no token and is not a reference, ensure token
        if not rec['flash_sets'][name].get('ref_token') and not rec['flash_sets'][name].get('token'):
            rec['flash_sets'][name]['token'] = uuid.uuid4().hex[:8]
    # Ensure active set points to this name if not set
    if not rec.get('flash_active_set'):
        rec['flash_active_set'] = name
    _write_flash_all(users)
    return True


def delete_flash_set(username: str, name: str) -> bool:
    """Delete a named flashcard set for user. Returns True on success."""
    users = _read_flash_all()
    key = (username or '').lower()
    rec = users.get(key)
    if not isinstance(rec, dict):
        return False
    sets = rec.get('flash_sets')
    if not isinstance(sets, dict) or name not in sets:
        return False
    # Capture token for cascading removal of imported references
    try:
        removed_token = (sets.get(name) or {}).get('token')
    except Exception:
        removed_token = None
    try:
        del sets[name]
    except Exception:
        return False
    # Adjust active set if we deleted the active one
    if rec.get('flash_active_set') == name:
        try:
            rec['flash_active_set'] = next(iter(sets.keys())) if sets else ''
        except Exception:
            rec['flash_active_set'] = ''
    # Cascade: remove any imported/reference sets in other users that point to this token
    try:
        if removed_token:
            for u_key, u_rec in list(users.items()):
                if not isinstance(u_rec, dict):
                    continue
                u_sets = u_rec.get('flash_sets') or {}
                if not isinstance(u_sets, dict):
                    continue
                for s_name in list(u_sets.keys()):
                    item = u_sets.get(s_name) or {}
                    ref_tok = item.get('ref_token')
                    ref_owner = item.get('ref_owner')
                    ref_title = item.get('ref_title')
                    if (isinstance(ref_tok, str) and ref_tok == removed_token) or \
                       ((ref_owner or '').lower() == key and (ref_title or '') == name):
                        try:
                            del u_sets[s_name]
                        except Exception:
                            continue
                        # Fix up active set for that user if needed
                        if u_rec.get('flash_active_set') == s_name:
                            try:
                                u_rec['flash_active_set'] = next(iter(u_sets.keys())) if u_sets else ''
                            except Exception:
                                u_rec['flash_active_set'] = ''
            # Also remove from flash_shares store if present
            try:
                from backend.flash_share import delete_share
                try:
                    delete_share(removed_token)
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        pass
    _write_flash_all(users)
    return True

def ensure_flash_set_token(username: str, name: str) -> str:
    """Ensure the named flash set has a token; create and persist if missing. Return token."""
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    if 'flash_sets' not in rec or not isinstance(rec['flash_sets'], dict):
        rec['flash_sets'] = {}
    # If this is a reference set, prefer ref_token and do not create an owner token
    if name in rec['flash_sets'] and isinstance(rec['flash_sets'][name], dict):
        ref_tok = rec['flash_sets'][name].get('ref_token')
        if isinstance(ref_tok, str) and ref_tok:
            return ref_tok
    if name not in rec['flash_sets']:
        # Create minimal set with token when missing (respecting limit)
        if len(rec['flash_sets']) >= FLASHCARD_MAX_SETS:
            # As a fallback, attach token to active set
            active = rec.get('flash_active_set') or ''
            if active and active in rec['flash_sets']:
                tok = rec['flash_sets'][active].get('token') or uuid.uuid4().hex[:8]
                rec['flash_sets'][active]['token'] = tok
                _write_flash_all(users)
                return tok
            # Otherwise generate a token unattached (rare)
            tok = uuid.uuid4().hex[:8]
            _write_flash_all(users)
            return tok
        rec['flash_sets'][name] = {'text': '', 'pool': [], 'token': uuid.uuid4().hex[:8]}
        if not rec.get('flash_active_set'):
            rec['flash_active_set'] = name
        _write_flash_all(users)
        return rec['flash_sets'][name]['token']
    tok = rec['flash_sets'][name].get('token')
    if not tok:
        tok = uuid.uuid4().hex[:8]
        rec['flash_sets'][name]['token'] = tok
        _write_flash_all(users)
    return tok


def get_flash_set_token(username: str, name: str) -> Optional[str]:
    # Return ref_token if present (for imported/reference sets); otherwise ensure/return owner token
    rec = _get_flash_user_record(username)
    sets = rec.get('flash_sets') or {}
    item = (sets.get(name) or {}) if isinstance(sets, dict) else {}
    ref_tok = item.get('ref_token')
    if isinstance(ref_tok, str) and ref_tok:
        return ref_tok
    # Owned set: ensure a token exists
    try:
        tok = item.get('token')
        if not tok:
            tok = ensure_flash_set_token(username, name)
        return str(tok) if tok else None
    except Exception:
        return None


def add_flash_set_ref(username: str, name: str, token: str, owner: str = '', title: str = '') -> bool:
    """Create/update a named set that references a shared FlashCard by token (no copy)."""
    users = _read_flash_all()
    key = (username or '').lower()
    if key not in users or not isinstance(users[key], dict):
        users[key] = {}
    rec = users[key]
    if 'flash_sets' not in rec or not isinstance(rec['flash_sets'], dict):
        rec['flash_sets'] = {}
    rec['flash_sets'][name] = {
        'ref_token': str(token or ''),
        'ref_owner': str(owner or ''),
        'ref_title': str(title or ''),
    }
    if not rec.get('flash_active_set'):
        rec['flash_active_set'] = name
    _write_flash_all(users)
    return True


