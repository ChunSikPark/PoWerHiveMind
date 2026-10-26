# Getting started, from zero

This page assumes nothing. If you have never installed Python and have never used an AI
coding agent, you are the person it is written for.

About fifteen minutes. Do the steps in order. **You will not type a single terminal
command**, only downloads, buttons, and one line pasted into a chat box.

---

## What you are setting up

| Piece | What it is for |
|---|---|
| **An AI coding agent** | The program that reads the knowledge and writes the code. Claude Code here |
| **Python** | The language your agent writes that code in |
| **This knowledge base** | Markdown files, not a program. It teaches your agent how PowerWorld really behaves. Step 4, one line |
| **Two Python packages** | `esapp` talks to PowerWorld, `TeamOverbyeWeather` fetches weather. Step 5 installs them for you |

You also need **PowerWorld Simulator** itself. You either have it through your university
or employer, or you do not. See [About the PowerWorld
licence](#about-the-powerworld-licence).

Throughout this page, **agent** means the program in row one. An agent can open your files
and run code on your computer. A chat window in a browser cannot, which is why this kit
needs one.

---

## Step 1 — Install Claude

Download it from **[claude.com/download](https://claude.com/download)**, run the installer,
and sign in.

**Downloading is not installing.** The download leaves a file in your `Downloads` folder
and nothing happens until you open it. Look for a file whose name starts with `Claude` and
ends in `.exe`, and double-click it.

Claude does not put an icon on your desktop, so an empty desktop does not mean it failed.
Open Start, type `Claude`, right-click the result, and choose **Pin to taskbar**.

**Two things must be true or nothing below works:**

| You need | Why |
|---|---|
| **A paid Claude plan** — Pro, Max, Team or Enterprise | The free plan does not include Claude Code. If the **Code** button asks you to upgrade, that is why |
| **Git** — [git-scm.com/downloads/win](https://git-scm.com/downloads/win) | Step 4 uses it to fetch the knowledge base. Click through the installer with every default |

You do **not** need Node.js. The Claude app already includes Claude Code.

Using Codex, Cursor or Windsurf instead? See [Other agents](#other-agents).

---

## Step 2 — Install Python

Go to [python.org/downloads](https://www.python.org/downloads/) and click the big download
button. Run the installer.

**On the first screen, tick "Add Python to PATH" before you click Install.**

This is the single most common thing to get wrong. The box is small, near the bottom, and
off by default. Miss it and later steps fail with errors that never mention Python.
Step 5 checks it for you.

---

## Step 3 — Open Claude Code

Open Claude. At the **top left** is a toggle with two halves: `Chat and Cowork` and `Code`.

**Click `Code`.**

![The Code button sits at the top left, next to Chat and Cowork](assets/desktop-code-toggle.png)

`Chat and Cowork` is ordinary conversation and cannot see your files. `Code` can. Landing
in the wrong one is a common way to get stuck.

---

## Step 4 — Install the knowledge base

Paste this into the box where you type and press Enter. It is a plain sentence asking
Claude to fetch something for you.

```
Install the PowerWorld knowledge base: git clone https://github.com/ChunSikPark/PoWerHiveMind ~/.claude/skills/powerhivemind
```

Claude downloads it into a folder it already watches. There is no folder to choose, no ZIP
to unzip, and nothing to remember the location of.

**Then load it.** Type:

```
/reload-plugins
```

**Closing and reopening the app is not enough.** It usually reopens the same conversation,
and a reopened conversation keeps whatever it started with. The knowledge stays
invisible and it looks like the install failed. `/reload-plugins` avoids that. Starting a
genuinely new conversation works too.

You do this once. Every conversation afterwards has the knowledge already.

**To update it later**, ask Claude to `git pull` in that folder. **To remove it**, delete
the folder.

---

## Step 5 — Check your machine

Type:

```
/powerhivemind:powerworld-setup
```

The `powerhivemind:` prefix is part of the name. Plain `/powerworld-setup` will not
work.

This installs the two Python packages and runs four quick checks. One of three things
happens.

> The other command the plugin registers is `/powerhivemind:kb-page`, which
> writes what you learn back into the kit as a new page. You do not need it yet. See
> [README.md](README.md) when you do.

**Everything passes.** It prints your PowerWorld **build date**. Keep a note of it, because
PowerWorld's behaviour changes between versions. Go to Step 6.

**It cannot find Python.** The "Add Python to PATH" box in Step 2 was not ticked. Re-run
the Python installer, choose **Modify**, turn on "Add Python to environment variables", and
run the command again.

**It fails on SimAuto or a licence.** Read [About the PowerWorld
licence](#about-the-powerworld-licence). No code change fixes this one.

---

## Step 6 — Prove it worked

Step 5 checked your machine. This checks that your agent got the knowledge, which can fail
separately.

**Open a folder that has nothing to do with PowerWorld** — any project, or an empty one.
The knowledge travels with you, and this proves it. Ask:

> Without running any code, tell me what happens if I call `pw.esa.SaveCase("out.pwb")`.

**Right answer: it silently writes no file.** The call reports success, no file appears,
and you have to use `RunScriptCommand('SaveCase("out.pwb", PWB);')` and check the file
exists afterwards.

**Wrong answer: it saves the case.** That is the reasonable guess from the method name, and
it is what any assistant says without these pages. If you get it, the knowledge did not
load:

- **The conversation predates the install.** Type `/reload-plugins`, or start a new
  conversation.
- **It landed somewhere else.** Ask Claude whether `~/.claude/skills/powerhivemind`
  exists and contains `AGENTS.md`. If not, redo Step 4.

You are done. Skip to [What to ask next](#what-to-ask-next).

---

## Other agents

Any agent that runs on your computer and can read your files works with this kit.

**Codex** has its own plugin marketplace and this repository ships a manifest for it:

```
codex plugin marketplace add ChunSikPark/PoWerHiveMind
```

Then open `/plugins`, install **powerhivemind**, and start a new session. *(Not yet
tested against a released Codex build. If it fails, use the manual route below and please
open an issue.)*

**Cursor, Windsurf, or anything else**: clone the repository and start your agent inside
the folder.

```
git clone https://github.com/ChunSikPark/PoWerHiveMind
```

No `git`? On the repository page, click the green **Code** button, then **Download ZIP**,
and unzip it somewhere you will find again.

Then point your agent at that folder (every agent has some way to open one) and ask:

> Read AGENTS.md. Check whether Python is installed, install the `esapp` and
> `TeamOverbyeWeather` packages if they are missing, then run the preflight check.

There is no `/powerhivemind:powerworld-setup` on this route; that request replaces it.

---

## About the PowerWorld licence

PowerWorld automation needs three things, and the third catches almost everyone.

1. **Windows.** The interface PowerWorld exposes for automation is Windows-only. There is
   no Mac or Linux version.
2. **PowerWorld Simulator, installed and licensed.**
3. **The SimAuto add-on, licensed separately.**

**SimAuto is a different licence from Simulator.** Your Simulator can open cases, run studies, and look completely healthy while
every line of automation fails, and nothing in the program tells you that is why.

If Step 5 fails on that check, no amount of changing the code will help. Ask whoever
administers your PowerWorld licence whether it includes SimAuto.

### Without a PowerWorld licence

**A small part still works.** Fetching and inspecting weather data is pure Python:
downloading ERA5, HRRR and NOAA data, and reading, cropping and combining `.pww` files.

That is where it stops. *Using* those files means PowerWorld's TimeStep feature, which runs
inside Simulator. Ask your agent:

> Download February 2021 weather for Texas.

That works on any machine, with no PowerWorld licence and no Windows.

---

## What to ask next

Ask in plain English. Your agent finds the right pages itself.

> Open my case at C:\path\to\case.pwb and summarize it.

> Which branches are most heavily loaded in this case?

> Run an N-1 contingency analysis and show me the worst violations.

> Add a 138 kV line between bus 12 and bus 40 and tell me what it does to overloads.

> Load this weather file and give me hourly wind and solar output for the renewable
> generators.

> Compare my 2016 and 2024 cases and tell me what the plan builds.

You do not need to know which page covers what. That is the agent's job.

---

## When something goes wrong

**I installed Claude but cannot find it.** Either the installer downloaded and was never
run: look in `Downloads` for a file starting with `Claude`, ending in `.exe`, and
double-click it. Or it did install and you are looking at the desktop, where Claude puts no
icon: open Start, type `Claude`, right-click, **Pin to taskbar**.

**There is no Code button.** Your app is an older version. Reinstall from
[claude.com/download](https://claude.com/download).

**Clicking Code asks me to upgrade.** Claude Code needs a paid plan. See Step 1.

**A slash command is not recognized.** For `/powerhivemind:powerworld-setup`, the
knowledge base is installed but this conversation has not loaded it. Type
`/reload-plugins`. Check the prefix too: plain `/powerworld-setup` is not its name. As for
`/plugin`, it does not exist in the desktop app at all; Step 4 does not need it.

**Claude cannot run `git`.** Git is not installed. See the table in Step 1.

**My agent does not seem to know about PowerWorld.** Type `/reload-plugins`, or start a new
conversation. On the manual route, it is pointed at the wrong folder. Tell it
`Read AGENTS.md in this folder.`

**The code it writes errors.** Ask it to check itself against the knowledge base: `Check
the preflight page and the relevant page. Is this the documented way to do it?`

**Everything fails with a COM or licence error.** See [About the PowerWorld
licence](#about-the-powerworld-licence). Not fixable in code.

**An answer looks wrong.** Ask which pages it used: `Which pages from this knowledge base
did you use?` If a page is wrong, open an issue saying which page and what it got wrong. Those reports are the most valuable ones this project gets.

---

## Where to go from here

- **[index.md](index.md)** — every page, one line each
- **[AGENTS.md](AGENTS.md)** — what your agent reads. Worth skimming to see what it knows
- **[README.md](README.md)** — the short version of this page
