import os
import threading
import time
import logging

from typing import Dict, Any

from . import bio_store
from .word_selector import WordSelector
from .openrouter_monitor import get_quota_warning


logger = logging.getLogger("backend.flashcard_worker")

_worker_started = False
_worker_lock = threading.Lock()


def _improve_flashcard_hints_once() -> None:
    """Run a single maintenance pass across users to (1) top up FlashCard pools to the
    configured target size and (2) upgrade local hints to API hints where possible.
    Respects per-word attempt caps, batch limits, and quota warnings.
    """
    try:
        # Load users_bio.json directly to iterate users
        users: Dict[str, Any] = bio_store._read_all()  # type: ignore[attr-defined]
    except Exception:
        users = {}

    if not isinstance(users, dict) or not users:
        return

    ws = WordSelector()
    # Check quota once per pass to avoid log spam
    try:
        _quota = get_quota_warning()
        _quota_critical = bool(_quota and _quota.get('level') == 'error')
    except Exception:
        _quota = None
        _quota_critical = False
    if _quota_critical:
        try:
            logger.warning("[FlashWorker] Critical quota; pausing upgrades for now.")
        except Exception:
            pass
    # Knobs
    try:
        max_attempts = int(os.getenv('PERSONAL_POOL_API_ATTEMPTS', '3'))
    except Exception:
        max_attempts = 3
    try:
        per_user_batch = int(os.getenv('FLASHCARD_WORKER_BATCH_PER_USER', '3'))
    except Exception:
        per_user_batch = 3
    try:
        topup_per_user = int(os.getenv('FLASHCARD_WORKER_TOPUP_PER_USER', '5'))
    except Exception:
        topup_per_user = 5
    try:
        target_size = int(os.getenv('FLASHCARD_POOL_MAX', '10'))
    except Exception:
        target_size = 10
    try:
        enable_topup = os.getenv('ENABLE_FLASHCARD_TOPUP', 'true').strip().lower() in ('1','true','yes','on')
    except Exception:
        enable_topup = True

    for username, rec in users.items():
        try:
            # New storage is per-user named sets in users.flashcards.json
            # Fallback to legacy structure if present
            active_name = ''
            pool = None
            text = ''
            try:
                active_name = bio_store.get_active_flash_set_name(username)  # type: ignore[attr-defined]
                pool = bio_store.get_flash_set_pool(username, active_name)   # type: ignore[attr-defined]
                text = bio_store.get_flash_set_text(username, active_name)   # type: ignore[attr-defined]
            except Exception:
                pool = rec.get('flash_pool') if isinstance(rec, dict) else None
            if not isinstance(pool, list):
                pool = []

            # 1) Top-up: if enabled and below target, add new words (local hints first)
            if enable_topup and len(pool) < target_size and text:
                added = 0
                try:
                    # Respect quota warnings for API attempts; still allow offline extraction
                    use_api = not _quota_critical
                except Exception:
                    use_api = True
                try:
                    if use_api:
                        new_items = ws._generate_flash_pool_api(text, max_items=topup_per_user)
                    else:
                        new_items = []
                except Exception:
                    new_items = []
                # Fallback to offline extraction if API yields few
                if len(new_items) < topup_per_user:
                    try:
                        candidates = ws._extract_flash_words(text, max_items=topup_per_user * 3)
                    except Exception:
                        candidates = []
                    existing = {str((it.get('word') if isinstance(it, dict) else it) or '').lower() for it in pool}
                    for w in candidates:
                        if added >= topup_per_user or len(pool) >= target_size:
                            break
                        wl = (w or '').strip().lower()
                        if not wl or wl in existing:
                            continue
                        hint_text = ws._make_flash_hint(w, text) or ws._first_letter_hint(w)
                        pool.append({'word': w, 'hint': hint_text, 'hint_source': 'local', 'api_attempts': 0})
                        existing.add(wl)
                        added += 1
                # Persist updated pool if anything was added
                if added > 0:
                    try:
                        if active_name:
                            bio_store.upsert_flash_set(username, active_name, text=text, pool=pool)  # type: ignore[attr-defined]
                        else:
                            bio_store.update_user_record(username, {'flash_pool': pool})  # type: ignore[attr-defined]
                    except Exception:
                        pass
            if not pool:
                continue
            updated_pool = []
            changed = False
            attempts_made = 0
            for item in pool:
                # Stop early per-user to avoid aggressive usage
                if attempts_made >= per_user_batch:
                    updated_pool.extend(pool[len(updated_pool):])
                    break
                if not isinstance(item, dict):
                    # normalize missing metadata
                    if isinstance(item, dict) and 'hint_source' not in item:
                        item['hint_source'] = 'api' if str(item.get('hint','')).strip() else 'local'
                    if isinstance(item, dict) and 'api_attempts' not in item:
                        item['api_attempts'] = 0
                    if isinstance(item, dict) and 'hint_source' not in item:
                        item['hint_source'] = 'api' if str(item.get('hint','')).strip() else 'local'
                    if isinstance(item, dict) and 'api_attempts' not in item:
                        item['api_attempts'] = 0
                    updated_pool.append(item)
                    continue
                w = str(item.get('word', '')).strip()
                hint = str(item.get('hint', '')).strip()
                src = item.get('hint_source', 'local')
                tries = int(item.get('api_attempts', 0))
                if w and src != 'api' and tries < max_attempts:
                    # Respect quota warnings (already logged once at pass start)
                    if _quota_critical:
                        updated_pool.append(item)
                        continue
                    # One API attempt this pass
                    got = None
                    try:
                        api_h = ws.get_api_hints_force(w, 'flashcard', n=1, attempts=1)
                        got = str(api_h[0]) if api_h else None
                    except Exception as e:
                        logger.info(f"[FlashWorker] API attempt failed for '{w}': {e}")
                        got = None
                    tries += 1
                    attempts_made += 1
                    if got:
                        updated_pool.append({"word": w, "hint": got, 'hint_source': 'api', 'api_attempts': tries})
                        changed = True
                    else:
                        updated_pool.append({"word": w, "hint": hint, 'hint_source': src, 'api_attempts': tries})
                        changed = True
                else:
                    updated_pool.append(item)
            if changed:
                try:
                    bio_store.update_user_record(username, {'flash_pool': updated_pool})
                    logger.debug(f"[FlashWorker] Upgraded flash_pool hints for user '{username}'.")
                except Exception:
                    pass
        except Exception:
            continue


def _improve_personal_hints_once() -> None:
    """Upgrade Personal pool items' hints to API-generated where missing, similar to FlashCard."""
    try:
        users: Dict[str, Any] = bio_store._read_all()  # type: ignore[attr-defined]
    except Exception:
        users = {}
    if not isinstance(users, dict) or not users:
        return
    ws = WordSelector()
    try:
        max_attempts = int(os.getenv('PERSONAL_POOL_API_ATTEMPTS', '3'))
    except Exception:
        max_attempts = 3
    try:
        per_user_batch = int(os.getenv('PERSONAL_WORKER_BATCH_PER_USER', '3'))
    except Exception:
        per_user_batch = 3
    for username, rec in users.items():
        try:
            pool = rec.get('personal_pool') if isinstance(rec, dict) else None
            if not isinstance(pool, list) or not pool:
                continue
            updated_pool = []
            changed = False
            attempts_made = 0
            for item in pool:
                if attempts_made >= per_user_batch:
                    updated_pool.extend(pool[len(updated_pool):])
                    break
                if not isinstance(item, dict):
                    updated_pool.append(item)
                    continue
                w = str(item.get('word', '')).strip()
                hint = str(item.get('hint', '')).strip()
                src = item.get('hint_source', 'api' if hint else 'local')
                tries = int(item.get('api_attempts', 0))
                if w and src != 'api' and tries < max_attempts:
                    warning = get_quota_warning()
                    if warning and warning.get('level') == 'error':
                        updated_pool.append(item)
                        continue
                    got = None
                    try:
                        ah = ws.get_api_hints_force(w, 'personal', n=1, attempts=1)
                        got = str(ah[0]) if ah else None
                    except Exception:
                        got = None
                    tries += 1
                    attempts_made += 1
                    if got:
                        updated_pool.append({"word": w, "hint": got, 'hint_source': 'api', 'api_attempts': tries})
                        changed = True
                    else:
                        updated_pool.append({"word": w, "hint": hint, 'hint_source': src, 'api_attempts': tries})
                        changed = True
                else:
                    updated_pool.append(item)
            if changed:
                try:
                    bio_store.update_user_record(username, {'personal_pool': updated_pool})
                except Exception:
                    pass
        except Exception:
            continue


def _worker_loop(interval: float) -> None:
    while True:
        try:
            enabled = os.getenv('ENABLE_FLASHCARD_BACKGROUND', 'true').strip().lower() in ('1','true','yes','on')
        except Exception:
            enabled = True
        if enabled:
            _improve_flashcard_hints_once()
            try:
                _improve_personal_hints_once()
            except Exception:
                pass
        time.sleep(max(5.0, interval))


def start_flashcard_worker() -> None:
    """Start the background worker if not already running and if enabled by env."""
    global _worker_started
    try:
        enabled = os.getenv('ENABLE_FLASHCARD_BACKGROUND', 'true').strip().lower() in ('1','true','yes','on')
    except Exception:
        enabled = True
    if not enabled:
        return
    with _worker_lock:
        if _worker_started:
            return
        try:
            try:
                interval = float(os.getenv('FLASHCARD_WORKER_INTERVAL_SECS', '60'))
            except Exception:
                interval = 60.0
            th = threading.Thread(target=_worker_loop, args=(interval,), daemon=True)
            th.start()
            _worker_started = True
            logger.info("[FlashWorker] FlashCard background worker started.")
        except Exception as e:
            logger.warning(f"[FlashWorker] Failed to start background worker: {e}")


