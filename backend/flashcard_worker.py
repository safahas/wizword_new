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
    """Run a single maintenance pass across users to upgrade local FlashCard hints to API hints.
    Respects per-word attempt caps and quota warnings. Makes at most a small batch of attempts per user per pass.
    """
    try:
        # Load users_bio.json directly to iterate users
        users: Dict[str, Any] = bio_store._read_all()  # type: ignore[attr-defined]
    except Exception:
        users = {}

    if not isinstance(users, dict) or not users:
        return

    ws = WordSelector()
    # Knobs
    try:
        max_attempts = int(os.getenv('PERSONAL_POOL_API_ATTEMPTS', '3'))
    except Exception:
        max_attempts = 3
    try:
        per_user_batch = int(os.getenv('FLASHCARD_WORKER_BATCH_PER_USER', '3'))
    except Exception:
        per_user_batch = 3

    for username, rec in users.items():
        try:
            pool = rec.get('flash_pool') if isinstance(rec, dict) else None
            if not isinstance(pool, list) or not pool:
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
                    updated_pool.append(item)
                    continue
                w = str(item.get('word', '')).strip()
                hint = str(item.get('hint', '')).strip()
                src = item.get('hint_source', 'local')
                tries = int(item.get('api_attempts', 0))
                if w and src != 'api' and tries < max_attempts:
                    # Respect quota warnings
                    warning = get_quota_warning()
                    if warning and warning.get('level') == 'error':
                        logger.warning("[FlashWorker] Critical quota; pausing upgrades for now.")
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
                    logger.info(f"[FlashWorker] Upgraded flash_pool hints for user '{username}'.")
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


