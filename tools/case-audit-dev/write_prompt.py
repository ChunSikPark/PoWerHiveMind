"""Write an eval case's prompt.md and case.yaml from its fixture, so the findings travel inline.

    python tools/case-audit-dev/write_prompt.py evals/<case> [evals/<case> ...]

Run it after replay.py or scrub_findings.py has written the case's fixtures/findings.md. The eval
sandbox does not expose `context.add_dirs` to the agent on native Windows, and `scaffold_script`
fails there, so the prompt carries the audit itself: the engineer's question (kept as it is), one
line saying the audit was already run, then findings.md verbatim in a fence. fixtures/ stays the
source of truth; the suite checks that each prompt still embeds it word for word.

The frontmatter also gets `append_system_prompt` (ROUTING): eval run 2 showed the main session
answering every case itself and never dispatching case-auditor. The question stays plain.
"""
import re
import sys
from pathlib import Path

INTRO = "PowerWorld isn't on this machine, but I already ran the case audit on it. Here is its findings.md:"
MARK = "PowerWorld isn't on this machine"   # where the question ends, in the old prompts and the new
ROUTING = ("You are the main session of the PoWerHiveMind kit. When the user asks about a PowerWorld "
           "case's readiness, health or contents, hand the request to the case-auditor agent with the Agent "
           "tool: pass the user's words and the audit output below verbatim, add nothing. Then relay the "
           "agent's final message to the user verbatim, once, adding nothing before or after it.")


def write(case: Path) -> None:
    text = (case / "prompt.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m or MARK not in m.group(2):
        raise SystemExit(f"{case}: prompt.md has no frontmatter or no '{MARK}' line to split on")
    keys = [k for k in m.group(1).split("\n") if not k.startswith("append_system_prompt:")]
    keys.append(f'append_system_prompt: "{ROUTING}"')     # double-quoted: the text holds ": "
    question = m.group(2).split(MARK)[0].strip()
    md = (case / "fixtures" / "findings.md").read_text(encoding="utf-8")
    front = "---\n" + "\n".join(keys) + "\n---\n"
    # LF on disk on every platform: the eval tool parses the frontmatter
    (case / "prompt.md").write_text(f"{front}\n{question}\n\n{INTRO}\n\n````markdown\n{md}````\n",
                                    encoding="utf-8", newline="\n")
    (case / "case.yaml").write_text(f'schema_version: "1.1"\nname: {case.name}\n', encoding="utf-8", newline="\n")
    print(f"{case.name}: prompt carries findings.md ({len(md):,} characters)")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        write(Path(arg))
