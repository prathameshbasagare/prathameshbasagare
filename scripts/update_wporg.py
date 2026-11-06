"""Refresh the WordPress.org plugin table in README.md.

Fetches every plugin published by the WordPress.org author below and rewrites
the block between the WPORG markers. Uses only the standard library.
"""

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

AUTHOR = "curiouswpdev"
README = Path(__file__).resolve().parent.parent / "README.md"
START = "<!-- WPORG:START -->"
END = "<!-- WPORG:END -->"


def fetch_plugins():
    query = urllib.parse.urlencode(
        {
            "action": "query_plugins",
            "request[author]": AUTHOR,
            "request[per_page]": 50,
        }
    )
    req = urllib.request.Request(
        f"https://api.wordpress.org/plugins/info/1.2/?{query}",
        headers={"User-Agent": f"{AUTHOR}-profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get("plugins", [])


def installs(n):
    return "<10" if n < 10 else f"{n:,}+"


def render(plugins):
    if not plugins:
        return "_No plugins found on WordPress.org._"
    plugins = sorted(plugins, key=lambda p: p.get("downloaded", 0), reverse=True)
    rows = [
        "| Plugin | Version | Tested up to | Active installs | Downloads | Last updated |",
        "| :-- | :-: | :-: | :-: | :-: | :-: |",
    ]
    for p in plugins:
        name = html.unescape(p.get("name", "")).replace("\u2014", "-")
        url = f"https://wordpress.org/plugins/{p['slug']}/"
        updated = str(p.get("last_updated", "")).split(" ")[0]
        rows.append(
            f"| [{name}]({url}) | {p.get('version', '')} | {p.get('tested', '')} "
            f"| {installs(int(p.get('active_installs', 0)))} | {int(p.get('downloaded', 0)):,} | {updated} |"
        )
    return "\n".join(rows)


def main():
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("WPORG markers not found in README.md")
    block = f"{START}\n{render(fetch_plugins())}\n{END}"
    new = pattern.sub(lambda _: block, text)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README.md updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
