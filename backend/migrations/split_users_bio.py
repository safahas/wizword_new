import os
import sys
import json
from datetime import datetime

def main() -> int:
    users_path = os.getenv('USERS_FILE', 'users.json')
    users_bio_path = os.getenv('USERS_BIO_FILE', 'users_bio.json')
    users_path = os.path.abspath(users_path)
    users_bio_path = os.path.abspath(users_bio_path)

    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception as e:
        print(f"Failed to read users.json: {e}")
        return 1

    bio_db = {}
    for username, rec in (users or {}).items():
        if not isinstance(rec, dict):
            continue
        entry = {}
        for k in ('bio', 'personal_pool'):
            v = rec.get(k)
            if v is not None:
                entry[k] = v
        if entry:
            bio_db[(username or '').lower()] = entry

    # Backup and write users_bio.json
    try:
        if os.path.exists(users_bio_path):
            ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            os.rename(users_bio_path, users_bio_path + '.bak.' + ts)
    except Exception:
        pass
    with open(users_bio_path, 'w', encoding='utf-8') as f:
        json.dump(bio_db, f, ensure_ascii=False, indent=2)

    # Strip moved fields from users.json and save
    changed = False
    for username, rec in (users or {}).items():
        if not isinstance(rec, dict):
            continue
        for k in ('bio', 'personal_pool'):
            if k in rec:
                rec.pop(k)
                changed = True
    if changed:
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    print(f"Moved bio/personal_pool to {users_bio_path}. Entries: {len(bio_db)}")
    return 0

if __name__ == '__main__':
    sys.exit(main())


