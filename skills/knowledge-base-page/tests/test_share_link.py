import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

KIT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KIT / "skills" / "knowledge-base-page" / "engine"))
import share_link  # noqa: E402

PAGE = "---\ntype: method\ntopic: contingency\n---\n\n# A page\n\n## Content\n\n```python\nx = 1  # 100% & done?\n```\n"


def query(url):
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_link_round_trips_title_body_and_label():
    url, body, fits = share_link.build("New page: methods/a-page.md", "Why: it bit me.", PAGE)
    q = query(url)
    assert fits and url.startswith(share_link.REPO + "?")
    assert q == {"title": "New page: methods/a-page.md", "body": body, "labels": "new-page,contingency"}
    assert " " not in url and "&done" not in url


def test_issue_carries_the_kind_and_the_topic_label():
    url, _, _ = share_link.build("Page update: methods/a-page.md", "n", PAGE, "page-defect")
    assert query(url)["labels"] == "page-defect,contingency"
    url, _, _ = share_link.build("Page update: methods/a-page.md", "n", PAGE, topic="design")
    assert query(url)["labels"] == "new-page,design"


def test_a_page_without_a_valid_topic_or_kind_is_refused():
    bare = PAGE.replace("topic: contingency\n", "")
    for page, kw in ((bare, {}), (PAGE.replace("contingency", "weather"), {}), (PAGE, {"label": "bug"})):
        with pytest.raises(ValueError):
            share_link.build("New page: methods/a-page.md", "note", page, **kw)


def test_page_fence_outlasts_the_fences_inside_it():
    body = share_link.issue_body("note", PAGE)
    assert body.count("````markdown") == 1 and body.rstrip().endswith("````")


def test_too_long_page_falls_back_to_note_and_paste_instruction():
    url, body, fits = share_link.build("Page update: concepts/big.md", "Note.", PAGE + "word " * 5000)
    assert not fits and len(url) <= share_link.LIMIT
    assert "Paste the full page" in query(url)["body"] and "word word" in body


def test_title_must_say_new_page_or_page_update():
    with pytest.raises(ValueError):
        share_link.build("my page", "note", PAGE)


def test_leftovers_flag_case_data_but_not_public_grids():
    text = "Ran on ERCOT_2027_summer.pwb from C:\\Users\\jdoe\\cases, mail jdoe@utility.com\nTexas2k: ACTIVSg2000.pwb, Hawaii40.pwb"
    hits = share_link.leftovers(text)
    assert [h.split(": ")[1] for h in hits] == ["case file name", "personal folder path", "email address"]
    assert not any("line 2" in h for h in hits)


def test_skill_runs_the_script_from_the_plugin_root_with_its_titles():
    skill = (KIT / "skills" / "knowledge-base-page" / "SKILL.md").read_text(encoding="utf-8")
    assert '"${CLAUDE_PLUGIN_ROOT}/skills/knowledge-base-page/engine/share_link.py"' in skill
    assert all(t.strip() in skill for t in share_link.TITLES) and "--label new-page" in skill
    assert all(f"`{t}`" in skill for t in share_link.TOPICS + share_link.KINDS)


def test_cli_writes_the_issue_body_next_to_the_copy(tmp_path, capsys):
    page, note = tmp_path / "a-page.md", tmp_path / "note.md"
    page.write_text(PAGE, encoding="utf-8")
    note.write_text("Why: it bit me.", encoding="utf-8")
    assert share_link.main(["--page", str(page), "--title", "New page: methods/a-page.md", "--note-file", str(note)]) == 0
    out = (tmp_path / "a-page.md.issue.md").read_text(encoding="utf-8")
    assert "x = 1" in out and share_link.REPO in capsys.readouterr().out
