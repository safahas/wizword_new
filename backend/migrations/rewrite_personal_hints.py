import os
import sys
import json
import time
import logging
from datetime import datetime

# Configure logging to stderr for debug details
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='[MIGRATE] %(message)s')
logger = logging.getLogger(__name__)


def _load_users(users_path: str) -> dict:
    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"users.json not found at: {users_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse users.json: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading users.json: {e}")
        return {}


def _save_users(users_path: str, users: dict) -> bool:
    try:
        # Backup first
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        backup_path = f"{users_path}.bak.{ts}"
        try:
            if os.path.exists(users_path):
                with open(users_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logger.info(f"Backup written: {backup_path}")
        except Exception as e:
            logger.warning(f"Backup skipped: {e}")

        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to write users.json: {e}")
        return False


def _should_rewrite(hint: str) -> bool:
    if hint is None:
        return True
    h = str(hint).strip().lower()
    if not h:
        return True
    # Common generic forms to replace
    generic_hints = {
        'from your bio',
        'from bio',
        'generic',
        'personal',
        'profile',
        'related to your profile'
    }
    return h in generic_hints


def _is_generic_word(word: str) -> bool:
    wl = (word or '').strip().lower()
    if not wl:
        return True
    number_words = {
        'zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty'
    }
    generic = {
        'have','since','and','the','this','that','these','those','with','without','about','into','onto',
        'from','by','for','as','at','to','in','of','on','a','an','is','are','was','were','be','been','am',
        'i','you','your','my','our','their','his','her','it','they','we','me','him','her','them',
        'people','person','thing','things','stuff','place','time','year','years','work','works','worked','working',
        'live','lived','living','like','likes','liked','watch','watched','watching','join','joined','joining',
        'use','used','using','most','many','life','day','days','good','bad','nice','great','hello','thanks','team'
    }
    return wl in generic or wl in number_words or wl.isdigit()


def main() -> int:
    # Resolve users.json path
    users_path = os.getenv('USERS_FILE', 'users.json')
    users_path = os.path.abspath(users_path)
    logger.info(f"Using users file: {users_path}")

    users = _load_users(users_path)
    if not isinstance(users, dict) or not users:
        logger.error("No users loaded; aborting.")
        return 1

    # Lazy import to avoid pulling Streamlit app
    try:
        # Ensure project root is on sys.path so 'backend' is importable
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from backend.word_selector import WordSelector
    except Exception as e:
        logger.error(f"Cannot import WordSelector: {e}")
        return 1

    ws = WordSelector()

    total_users = 0
    total_items = 0
    rewritten = 0
    removed = 0
    for username, rec in users.items():
        try:
            pool = rec.get('personal_pool')
            if not isinstance(pool, list) or not pool:
                continue
            total_users += 1
            new_pool = []
            for item in pool:
                if not isinstance(item, dict):
                    continue
                word = str(item.get('word') or '').strip()
                if not word or _is_generic_word(word):
                    # Skip adding generic tokens like 'have', 'since', etc.
                    removed += 1
                    continue
                total_items += 1
                hint = item.get('hint')
                # Force rewrite for specific awkward tokens
                force = word.lower() in {'high'}
                if _should_rewrite(hint) or force:
                    try:
                        new_hint = ws._make_profile_hint(word, rec)
                        if new_hint and new_hint != hint:
                            item['hint'] = new_hint
                            rewritten += 1
                    except Exception as e:
                        logger.warning(f"Hint build failed for user={username}, word={word}: {e}")
                new_pool.append(item)
            rec['personal_pool'] = new_pool
        except Exception as e:
            logger.warning(f"Skipping user={username} due to error: {e}")

    if rewritten or removed:
        ok = _save_users(users_path, users)
        if not ok:
            logger.error("Failed saving updated users.json")
            return 2

    # Clean summary to stdout
    print(f"users: {total_users}, items: {total_items}, rewritten: {rewritten}, removed: {removed}")
    logger.info("Migration complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())


