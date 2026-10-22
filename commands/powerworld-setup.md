---
description: Install the Python packages this kit needs and check whether PowerWorld can be driven from this machine
---

# PowerWorld setup

Get this machine ready to run the PowerWorld knowledge base. Two things happen: the Python
packages get installed, and the preflight says whether PowerWorld is drivable at all.

Work through the steps in order and stop at the first one that fails. **Report which step
failed and what it printed.** Do not carry on to the next step hoping it resolves itself,
and do not start writing analysis code afterwards: this command only sets up.

## 1. Find Python

```bash
python --version
```

No Python, or a version below 3.9: stop and tell the user to install it from
[python.org/downloads](https://www.python.org/downloads/), **ticking "Add Python to PATH"
on the first installer screen**. That checkbox is unticked by default and is the single
most common thing to get wrong here. Nothing below works without it.

On Windows, try `py --version` if `python` is not found. A working Python can still be
missing from `PATH`.

## 2. Install the packages

```bash
python -m pip install --upgrade esapp TeamOverbyeWeather pywin32 openpyxl
```

- `esapp` drives PowerWorld through SimAuto.
- `TeamOverbyeWeather` downloads the `.pww` weather files.
- `pywin32` is the COM bridge esapp calls through. On non-Windows it will not install, and
  that is expected (see step 3).
- `openpyxl` reads the PowerWorld field export behind the `schema-lookup` skill.

If pip is missing, `python -m ensurepip --upgrade` first.

Then confirm the install landed in **the same interpreter**, using the same `python` command
that ran pip:

```bash
python -c "import sys, esapp; print(sys.executable); print(esapp.__file__)"
```

If that raises `ModuleNotFoundError`, pip installed somewhere else: stop and report both
paths. Run this, and the preflight below, with plain `python`, never `python -I`. Isolated
mode hides the user site-packages, where a `--user` install puts esapp, and reports it
missing when it is there.

## 3. Run the preflight

Call `preflight_machine()` from the script in
`${CLAUDE_PLUGIN_ROOT}/methods/preflight-powerworld.md`, with the same `python` as step 2. It runs checks 1 to 4 (the
platform, `pywin32`, `esapp`, and the SimAuto COM server) and needs no case file. **Read
that page and use its script**; do not write your own version from memory. Leave check 5
(`preflight_case`) alone: the user has not given you a case yet.

**Report the Simulator version, not only the build date the preflight prints.** PowerWorld's
behaviour shifts between versions and it shifts silently, so the version belongs in every
session's opening report. On the same SimAuto object the preflight opened, read
`sa.ProgramInformation[0]`: it returns `('version', <major>, <build date>, <release label>)`,
such as `('version', 24, 2026-09-25, '25 beta')`. Report the **release label**, because a beta
keeps the previous major number (see way 1 in
`${CLAUDE_PLUGIN_ROOT}/concepts/version-requirements.md`). Compare it with the versions that
page lists as tested, and tell the user in one line:

- **A tested major version:** "You're on Simulator <n>, which HiveMind was tested on."
- **Any other:** "You're on Simulator <n>. HiveMind was tested on <tested versions>. Most of it
  should work, but if a command fails, the version is a likely cause."

Do not name commands that will fail: the page has no per-command list, only what was tested.

## 4. Say what the result means

A preflight failure is a fact about the machine, not a bug in the code. Give the user the
plain reading of it:

| What failed | What to tell them |
|---|---|
| Platform is not Windows | SimAuto is a Windows COM server and there is no port. The weather half of the kit still works: `${CLAUDE_PLUGIN_ROOT}/methods/teamoverbyeweather-client.md` |
| `pywin32` or `esapp` missing after step 2 | pip installed into a different interpreter than the one running the preflight. Print `sys.executable` from both and reconcile |
| SimAuto will not start | Usually Simulator is not installed, or is installed but has never been run once as administrator to register its COM server |
| A licence / "not authorized" / add-on error | **The SimAuto add-on is licensed separately from Simulator.** No code change fixes this. They need whoever administers their PowerWorld licence. Simulator's own GUI gives no hint of it and works fine |

The full failure table, with the exact error strings, is in the preflight page.

## 5. Offer the PWHM tag

Ask once, in plain words, and change nothing unless the user says yes:

> Do you use Claude Code in a terminal? If so, I can add a PWHM dashboard to your status
> line: the kit's version (and when a new one is out), the model, your 5-hour and weekly
> usage limits, and how full the context is. It doesn't show in the desktop app.

If they already have a status line, say instead that only the `[PWHM#<version>]` tag is added,
next to what they have, since their own already covers the rest.

Skip this step without asking if the user's status line already shows `[PWHM#`.

If they say yes:

1. Read `~/.claude/settings.json` and copy it to `~/.claude/settings.json.pwhm-backup` before
   changing anything.
2. **If a `statusLine` is already set, keep it.** Say so in one line: *"You already have a
   status line; the tag goes next to it and nothing of yours is replaced."* Write its
   `command` string, unchanged, to `~/.claude/powerworld-hivemind-statusline.json` as
   `{"previous": "<that command>"}`.
3. Set `statusLine` to `{"type": "command", "command": "\"<python>\" \"<kit root>/statusline/pwhm_statusline.py\""}`,
   where `<python>` is the full path from `python -c "import sys; print(sys.executable)"` and
   `<kit root>` is `${CLAUDE_PLUGIN_ROOT}` written out as an absolute path with forward
   slashes. Settings files don't expand variables.
4. Run that command once with `echo {} |` in front, and confirm the output contains `[PWHM#`.
5. Tell them it appears on the next refresh, and that saying *"remove the PWHM tag"* undoes it:
   put back the `statusLine` from `powerworld-hivemind-statusline.json` (or remove the key if
   that file doesn't exist), then delete that file.

## 6. Then stop

Say what passed, the Simulator version and build date, and, if it failed, which check and what it
means. Do not begin an analysis. Ask the user what they want to do next; if they have a
case file, `${CLAUDE_PLUGIN_ROOT}/methods/esapp-overview.md` is the next page.
