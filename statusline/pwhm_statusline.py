"""The PoWerHiveMind tag for Claude Code's terminal status line.

Prints [PWHM#0.4.0], plus a yellow "↑0.5.0 available" when the kit's daily update check has
seen a newer version. With no status line of the user's own, it also shows a dashboard: model,
5-hour and weekly usage limits, context used, and the session's time and cost, all read from
the JSON Claude Code sends. Status lines render in the terminal only, not in the desktop app.

/powerworld-hivemind:powerworld-setup adds it only when the user says yes. If they already
had a status line, setup saves that command to ~/.claude/powerworld-hivemind-statusline.json;
this script runs it on the same input and puts the tag beside it, so nothing is replaced.
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home() / ".claude"
VERSION_CACHE = HOME / "powerworld-hivemind-version.json"
SAVED = HOME / "powerworld-hivemind-statusline.json"
SEP = "\x1b[2m | \x1b[0m"
OMC_TAG = re.compile(r"(\x1b\[1m\[OMC#[^\]]*\]\x1b\[0m)")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tag():
    version = lambda v: tuple(int(p) for p in str(v).split(".") if p.isdigit())
    local = read_json(ROOT / ".claude-plugin" / "plugin.json").get("version", "?")
    latest = read_json(VERSION_CACHE).get("latest", "")
    out = f"\x1b[1m[PWHM#{local}]\x1b[0m"
    if latest and version(latest) > version(local):
        out += f" \x1b[33m↑{latest} available\x1b[0m"
    return out


def previous(data):
    command = read_json(SAVED).get("previous")
    if not command:
        return ""
    try:
        r = subprocess.run(command, shell=True, input=data, capture_output=True, timeout=5)
        return r.stdout.decode("utf-8", "replace").rstrip("\n")
    except (OSError, subprocess.SubprocessError):
        return ""


def color(pct):
    return "\x1b[32m" if pct < 70 else "\x1b[33m" if pct < 90 else "\x1b[31m"


def bar(pct, width):
    filled = round(pct / 100 * width)
    return f"[{color(pct)}{'#' * filled}\x1b[2m{'-' * (width - filled)}\x1b[0m]{color(pct)}{round(pct)}%\x1b[0m"


def until(reset):
    """Time left until a reset given as epoch seconds, epoch ms or an ISO string: 3h1m, 6d8h."""
    try:
        t = float(reset)
        t = t / 1000 if t > 1e12 else t
    except (TypeError, ValueError):
        try:
            t = datetime.fromisoformat(str(reset).replace("Z", "+00:00")).timestamp()
        except ValueError:
            return ""
    s = max(0, int(t - time.time()))
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    return f"\x1b[2m({d}d{h}h)\x1b[0m" if d else f"\x1b[2m({h}h{m}m)\x1b[0m"


def tokens(n):
    return f"{n / 1e6:.1f}M".replace(".0M", "M") if n >= 1e6 else f"{round(n / 1e3)}k"


def dashboard(info):
    """Model, usage limits, context and session, from the JSON Claude Code sends. A number it
    doesn't send is left out, never guessed."""
    parts = []
    model = (info.get("model") or {}).get("display_name") or (info.get("model") or {}).get("id")
    if model:
        parts.append(f"\x1b[36mModel: {model}\x1b[0m")
    limits = []
    for key, label in (("five_hour", "5h"), ("seven_day", "wk")):
        lim = (info.get("rate_limits") or {}).get(key) or {}
        if isinstance(lim.get("used_percentage"), (int, float)):
            limits.append(f"\x1b[2m{label}:\x1b[0m{bar(lim['used_percentage'], 8)}{until(lim.get('resets_at'))}")
    if limits:
        parts.append(" ".join(limits))
    ctx = info.get("context_window") or {}
    size, pct = ctx.get("context_window_size"), ctx.get("used_percentage")
    use = ctx.get("current_usage") or {}
    used = sum(use.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    if not isinstance(pct, (int, float)) and size and used:
        pct = used / size * 100
    if isinstance(pct, (int, float)):
        detail = f" \x1b[2m{tokens(used)}/{tokens(size)}\x1b[0m" if used and size else ""
        parts.append(f"ctx:{bar(pct, 10)}{detail}")
    cost = info.get("cost") or {}
    session = []
    if isinstance(cost.get("total_duration_ms"), (int, float)):
        session.append(f"{int(cost['total_duration_ms'] // 60000)}m")
    if isinstance(cost.get("total_cost_usd"), (int, float)):
        session.append(f"${cost['total_cost_usd']:.2f}")
    if session:
        parts.append("session:\x1b[32m" + " ".join(session) + "\x1b[0m")
    return SEP.join(parts)


def main():
    data = sys.stdin.buffer.read()
    t, prev = tag(), previous(data)
    if OMC_TAG.search(prev):
        out = OMC_TAG.sub(lambda m: m.group(1) + SEP + t, prev, count=1)
    elif prev:
        out = t + SEP + prev
    else:
        # No status line of their own: the tag brings the whole dashboard.
        try:
            info = json.loads(data.decode("utf-8") or "{}")
        except ValueError:
            info = {}
        board = dashboard(info)
        out = t + SEP + board if board else t
    sys.stdout.buffer.write(out.encode("utf-8"))


if __name__ == "__main__":
    main()
