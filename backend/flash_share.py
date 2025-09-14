import os
import json
import uuid
import time
from typing import Dict, Any, Optional, List

FLASH_SHARE_FILE = os.getenv('FLASH_SHARE_FILE', 'game_data/flash_shares.json')


def _ensure_store() -> None:
	os.makedirs(os.path.dirname(FLASH_SHARE_FILE) or '.', exist_ok=True)
	if not os.path.exists(FLASH_SHARE_FILE):
		with open(FLASH_SHARE_FILE, 'w', encoding='utf-8') as f:
			f.write('{}')


def _read_all() -> Dict[str, Any]:
	_ensure_store()
	try:
		with open(FLASH_SHARE_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data if isinstance(data, dict) else {}
	except Exception:
		return {}


def _write_all(data: Dict[str, Any]) -> None:
	_ensure_store()
	with open(FLASH_SHARE_FILE, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def generate_token() -> str:
	"""Generate a short share token."""
	# 8-char token from uuid4
	return uuid.uuid4().hex[:8]


def save_share(owner: str, title: str, pool: List[Dict[str, Any]], expires_at_utc: Optional[float] = None, token_override: Optional[str] = None) -> str:
	"""Create or update a shared flashcard set and return its token.

	owner: username (lowercase)
	title: descriptive title (e.g., category/topic)
	pool: list of items like {"word": str, "hint": str, "hint_source": str}
	expires_at_utc: optional epoch seconds for expiration
	"""
	data = _read_all()
	# Try to reuse an existing token if same owner+title already exists
	for tok, rec in data.items():
		if isinstance(rec, dict) and rec.get('owner') == (owner or '').lower() and rec.get('title') == (title or ''):
			rec['pool'] = pool or []
			rec['updated_at_utc'] = time.time()
			if expires_at_utc is not None:
				rec['expires_at_utc'] = expires_at_utc
			# If caller provided a token_override (set's token), and it differs, move the record under that token
			new_token = (token_override or '').strip()
			if new_token and new_token != tok:
				# Reassign entry under new token and delete old
				data[new_token] = dict(rec)
				try:
					del data[tok]
				except Exception:
					pass
				_write_all(data)
				return new_token
			_write_all(data)
			return tok
	# Create new
	token = (token_override or '').strip() or generate_token()
	data[token] = {
		'owner': (owner or '').lower(),
		'title': title or '',
		'pool': pool or [],
		'created_at_utc': time.time(),
		'updated_at_utc': time.time(),
		'expires_at_utc': expires_at_utc
	}
	_write_all(data)
	return token


def load_share(token: str) -> Optional[Dict[str, Any]]:
	"""Load a shared flashcard set by token. Returns None if missing or expired."""
	if not token:
		return None
	data = _read_all()
	rec = data.get(token)
	if not isinstance(rec, dict):
		return None
	# Check expiration
	exp = rec.get('expires_at_utc')
	if isinstance(exp, (int, float)) and exp and time.time() > float(exp):
		return None
	return rec


def list_shares_by_owner(owner: str) -> List[Dict[str, Any]]:
	"""Return metadata for shares owned by a user (no pools)."""
	data = _read_all()
	out: List[Dict[str, Any]] = []
	for tok, rec in data.items():
		if isinstance(rec, dict) and rec.get('owner') == (owner or '').lower():
			out.append({
				'token': tok,
				'title': rec.get('title') or '',
				'updated_at_utc': rec.get('updated_at_utc'),
				'expires_at_utc': rec.get('expires_at_utc')
			})
	return out


def import_share_to_user(token: str, username: str, set_name: Optional[str] = None) -> bool:
	"""Copy shared pool into user's named flashcard set (or active set).

	If set_name is provided and doesn't exist, will create if under the per-user limit.
	"""
	from backend.bio_store import set_flash_pool, upsert_flash_set, set_active_flash_set_name
	rec = load_share(token)
	if not rec:
		return False
	pool = rec.get('pool') or []
	uname = (username or '').lower()
	if set_name:
		ok = upsert_flash_set(uname, set_name, pool=pool)
		if not ok:
			return False
		set_active_flash_set_name(uname, set_name)
	else:
		set_flash_pool(uname, pool)
	return True
