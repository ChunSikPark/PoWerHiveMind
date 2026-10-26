"""Tell the user when a newer PoWerHiveMind is published.

Runs at session start. Reads this copy's version, asks GitHub for the published one at most
once a day, and says one line when the published one is newer. It edits nothing, and any
failure (offline, GitHub down, no cache) ends silently. Set PWHM_NO_UPDATE_CHECK=1 to turn it
off.

The result is cached in ~/.claude/powerhivemind-version.json, which a status line can
also read.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

LATEST_URL = "https://raw.githubusercontent.com/ChunSikPark/PoWerHiveMind/main/.claude-plugin/plugin.json"
CACHE = Path.home() / ".claude" / "powerhivemind-version.json"
DAY = 24 * 3600


def version_tuple(v):
    return tuple(int(p) for p in str(v).split(".") if p.isdigit())


def fetch_latest():
    with urllib.request.urlopen(LATEST_URL, timeout=3) as r:
        return json.load(r)["version"]


def main():
    if os.environ.get("PWHM_NO_UPDATE_CHECK"):
        return
    root = Path(__file__).resolve().parent.parent
    local = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    fresh = cache.get("latest") and time.time() - cache.get("checked", 0) < DAY
    new = cache["latest"] if fresh else fetch_latest()
    checked = cache["checked"] if fresh else time.time()
    if not fresh or local != cache.get("local"):
        CACHE.write_text(json.dumps({"local": local, "latest": new, "checked": checked}), encoding="utf-8")
    if version_tuple(new) > version_tuple(local):
        notify(local, new)


def notify(local, new):
    # A SessionStart hook can only reach the model: Claude Code discards `systemMessage` for this
    # event. So the note asks Claude to pass it on, once.
    root = Path(__file__).resolve().parent.parent.as_posix()
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": (
            f"PoWerHiveMind {new} is published; this copy is {local}. Start your first reply "
            f'with one line telling the user, e.g. "PoWerHiveMind {new} is out (you have '
            f'{local}). Want me to update it?" Say it once. If they agree, run `git pull` in '
            f"{root}, then tell them to run /reload-plugins."),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
