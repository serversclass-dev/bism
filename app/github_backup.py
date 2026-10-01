import os
import json
import base64
import urllib.request
import urllib.error
import threading
import time
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GITHUB_TOKEN  = "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"       # set manually in env
GITHUB_REPO   = "serversclass-dev/bism"        # e.g. "username/bims-data"
GITHUB_BRANCH = os.environ.get('GITHUB_BRANCH', 'main')
BACKUP_INTERVAL = 3600  # seconds (1 hour)

DATA_FILES = [
    'users', 'clients', 'suppliers', 'products',
    'inventory', 'orders', 'purchases', 'payments', 'settings'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _headers():
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'BIMS-Backup/1.0'
    }

def _api(path):
    return f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'

def _get_file(filename):
    """Fetch a file from GitHub. Returns (content_str, sha) or (None, None)."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return None, None
    try:
        url = _api(f'data/{filename}.json')
        req = urllib.request.Request(url, headers=_headers())
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            content = base64.b64decode(data['content']).decode('utf-8')
            return content, data.get('sha', '')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        print(f'[BACKUP] GET error {filename}: {e}')
        return None, None
    except Exception as e:
        print(f'[BACKUP] GET exception {filename}: {e}')
        return None, None

def _put_file(filename, content_str, sha=None):
    """Upload/update a file on GitHub."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False
    try:
        url     = _api(f'data/{filename}.json')
        encoded = base64.b64encode(content_str.encode('utf-8')).decode()
        payload = {
            'message': f'[BIMS] backup {filename} @ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC',
            'content': encoded,
            'branch':  GITHUB_BRANCH,
        }
        if sha:
            payload['sha'] = sha
        data = json.dumps(payload).encode('utf-8')
        req  = urllib.request.Request(url, data=data, headers=_headers(), method='PUT')
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception as e:
        print(f'[BACKUP] PUT error {filename}: {e}')
        return False

# ─── RESTORE ON FIRST RUN ─────────────────────────────────────────────────────

def restore_from_github():
    """
    Smart first-run sync:
    - Check if GitHub repo has ANY data file.
    - YES → pull ALL files from GitHub → overwrite local (server was reset, restore everything).
    - NO  → push ALL local files to GitHub (first ever run, seed the repo).
    Then start hourly backup.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print('[BACKUP] GitHub not configured — skipping sync.')
        return

    print('[BACKUP] 🔍 Checking GitHub repo for existing data...')
    os.makedirs(DATA_DIR, exist_ok=True)

    # Check if GitHub has at least one data file
    github_has_data = False
    for name in DATA_FILES:
        content, _ = _get_file(name)
        if content:
            try:
                parsed = json.loads(content)
                if parsed:  # non-empty list/dict
                    github_has_data = True
                    break
            except Exception:
                pass

    if github_has_data:
        # ── RESTORE: pull from GitHub → overwrite local
        #    If a file is missing on GitHub → push local copy up
        print('[BACKUP] ✅ GitHub has data → Syncing all files...')
        for name in DATA_FILES:
            local_path = os.path.join(DATA_DIR, f'{name}.json')
            content, sha = _get_file(name)
            if content is not None:
                # GitHub has this file → restore to local
                try:
                    parsed = json.loads(content)
                    with open(local_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed, f, ensure_ascii=False, indent=2)
                    print(f'[BACKUP]   ✅ Restored {name}.json ← GitHub')
                except Exception as e:
                    print(f'[BACKUP]   ⚠️  Failed to restore {name}: {e}')
            else:
                # GitHub missing this file → push local up
                if os.path.exists(local_path):
                    try:
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_content = f.read()
                        ok = _put_file(name, local_content, None)
                        if ok:
                            print(f'[BACKUP]   ✅ Pushed {name}.json → GitHub (was missing)')
                        else:
                            print(f'[BACKUP]   ❌ Failed to push {name}.json')
                    except Exception as e:
                        print(f'[BACKUP]   ⚠️  {name}: {e}')
                else:
                    print(f'[BACKUP]   — {name}.json missing locally and on GitHub, skipping.')
    else:
        # ── SEED: push all local files → GitHub (first ever run) ──
        print('[BACKUP] 🆕 GitHub is empty → Seeding GitHub from local files...')
        for name in DATA_FILES:
            local_path = os.path.join(DATA_DIR, f'{name}.json')
            if not os.path.exists(local_path):
                continue
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                _, sha = _get_file(name)
                ok = _put_file(name, content, sha)
                if ok:
                    print(f'[BACKUP]   ✅ Seeded {name}.json → GitHub')
                else:
                    print(f'[BACKUP]   ❌ Failed to seed {name}.json')
            except Exception as e:
                print(f'[BACKUP]   ⚠️  {name}: {e}')

    print('[BACKUP] 🎉 Initial sync complete.')

# ─── BACKUP TO GITHUB ─────────────────────────────────────────────────────────

def backup_to_github():
    """Upload all local data files to GitHub."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return

    print(f'[BACKUP] Starting backup @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    success = 0
    for name in DATA_FILES:
        local_path = os.path.join(DATA_DIR, f'{name}.json')
        if not os.path.exists(local_path):
            continue
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Get current SHA (needed for updates)
            _, sha = _get_file(name)
            ok = _put_file(name, content, sha)
            if ok:
                success += 1
                print(f'[BACKUP] ✅ {name}.json uploaded.')
            else:
                print(f'[BACKUP] ❌ {name}.json failed.')
        except Exception as e:
            print(f'[BACKUP] ❌ {name}: {e}')

    print(f'[BACKUP] Done. {success}/{len(DATA_FILES)} files backed up.')

# ─── BACKGROUND SCHEDULER ─────────────────────────────────────────────────────

def _scheduler():
    """Runs in a background thread — backs up every BACKUP_INTERVAL seconds."""
    while True:
        time.sleep(BACKUP_INTERVAL)
        try:
            backup_to_github()
        except Exception as e:
            print(f'[BACKUP] Scheduler error: {e}')

def start_backup_scheduler():
    """Start the background backup thread (daemon so it dies with the app)."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print('[BACKUP] GitHub token/repo not set — auto-backup disabled.')
        print('[BACKUP] Set GITHUB_TOKEN and GITHUB_REPO env vars to enable.')
        return
    t = threading.Thread(target=_scheduler, daemon=True, name='BackupScheduler')
    t.start()
    print(f'[BACKUP] ✅ Auto-backup started (every {BACKUP_INTERVAL//60} min).')