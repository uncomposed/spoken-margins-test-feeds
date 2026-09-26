#!/usr/bin/env python3
"""Generate fake "paid" podcast feeds for testing Spoken Margins link privacy.

Every token here is made up. The feeds copy the shapes real paid feeds use
(Patreon, Supercast, Substack) so the app's link policy can be tested end to end.
Run: python3 build.py   (needs macOS `say` for the audio)
"""
import os
import subprocess
from email.utils import formatdate
from xml.sax.saxutils import escape, quoteattr

BASE = "https://uncomposed.github.io/spoken-margins-test-feeds"
SHOW = "Spoken Margins Test Show"
SUBSCRIBERS = {
    "a": "FAKEsubA7f3a9c2e41b8d6a5c4b3e2f1a0d9c8b7",
    "b": "FAKEsubB1e2d3c4b5a69788776655443322110ff",
}

EPISODES = {
    "ep1": ("Episode 1: Why links leak", [
        "This is episode one of the Spoken Margins test show. Nothing in this feed is real.",
        "It exists so the app can be tested against the kinds of links that paid podcasts use.",
        "A paid feed is an ordinary web link with a secret built into it.",
        "Whoever holds that link can listen as the subscriber who owns it.",
        "So when a listener shares a Margin, the packet must never carry that secret.",
        "Here is a good place to record a Margin, about thirty seconds in.",
        "The recipient should still find this episode by its title, its show, and its length.",
        "That is the whole idea. Share the thought, not the key.",
        "The rest of this episode is a slow count, so there is room to test placement.",
        "One. Two. Three. Four. Five. Six. Seven. Eight. Nine. Ten.",
        "Eleven. Twelve. Thirteen. Fourteen. Fifteen. Sixteen. Seventeen. Eighteen. Nineteen. Twenty.",
        "This is the end of episode one.",
    ]),
    "ep2": ("Episode 2: Tokens in the path", [
        "This is episode two of the Spoken Margins test show.",
        "In this episode the secret sits in the path of the audio link, not in a query.",
        "Some hosts do this because it looks tidier, and it is just as easy to leak.",
        "A good moment for a Margin is right about here.",
        "Now a slow count for placement tests.",
        "Twenty one. Twenty two. Twenty three. Twenty four. Twenty five.",
        "Twenty six. Twenty seven. Twenty eight. Twenty nine. Thirty.",
        "Thirty one. Thirty two. Thirty three. Thirty four. Thirty five.",
        "This is the end of episode two.",
    ]),
    "ep3": ("Episode 3: When the GUID is the link", [
        "This is episode three of the Spoken Margins test show.",
        "Some feeds reuse the audio link as the episode's unique identifier.",
        "If that link carries a subscriber token, the identifier carries it too.",
        "The app has to treat that identifier like any other private link.",
        "Record a Margin here if you like.",
        "Now a slow count. Forty. Forty one. Forty two. Forty three. Forty four. Forty five.",
        "Forty six. Forty seven. Forty eight. Forty nine. Fifty.",
        "This is the end of episode three.",
    ]),
}


def make_audio(key, lines, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        return
    text = " [[slnc 700]] ".join(lines)
    subprocess.run(["say", "-v", "Samantha", "-r", "150", "-o", out_path,
                    "--file-format=m4af", "--data-format=aac", text], check=True)


def duration_seconds(path):
    out = subprocess.run(["afinfo", path], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        if "estimated duration" in line:
            return int(float(line.split(":")[1].split()[0]))
    raise RuntimeError("no duration for " + path)


def feed_xml(title, feed_url, episode_key, audio_url, guid, audio_path, is_permalink=False):
    ep_title, _ = EPISODES[episode_key]
    seconds = duration_seconds(audio_path)
    size = os.path.getsize(audio_path)
    pub = formatdate(1788220800 + int(episode_key[-1]) * 86400, usegmt=True)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(title)}</title>
    <link>{escape(BASE)}/</link>
    <atom:link href={quoteattr(feed_url)} rel="self" type="application/rss+xml"/>
    <description>Test fixture for Spoken Margins. All tokens are fake.</description>
    <language>en-us</language>
    <itunes:author>Spoken Margins</itunes:author>
    <item>
      <title>{escape(ep_title)}</title>
      <guid isPermaLink="{'true' if is_permalink else 'false'}">{escape(guid)}</guid>
      <pubDate>{pub}</pubDate>
      <enclosure url={quoteattr(audio_url)} length="{size}" type="audio/mp4"/>
      <itunes:duration>{seconds}</itunes:duration>
      <description>Test episode. The subscriber token in this feed is fake.</description>
    </item>
  </channel>
</rss>
"""


def write(path, text):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def main():
    for key, (_, lines) in EPISODES.items():
        make_audio(key, lines, f"audio/{key}.m4a")

    # Public control: no secrets anywhere. Links should survive sharing unchanged.
    write("feeds/public/show.rss", feed_xml(
        SHOW, f"{BASE}/feeds/public/show.rss", "ep1",
        f"{BASE}/audio/ep1.m4a", "smtf-ep1", "audio/ep1.m4a"))

    for name, token in SUBSCRIBERS.items():
        # 1. Patreon-style: token in the feed's query and in the audio link's query.
        write(f"feeds/subscriber-{name}/query-token.rss", feed_xml(
            f"{SHOW} (subscriber {name.upper()})",
            f"{BASE}/feeds/subscriber-{name}/query-token.rss?auth={token}", "ep1",
            f"{BASE}/audio/ep1.m4a?token-time=1790000000&token-hash={token}",
            "smtf-ep1", "audio/ep1.m4a"))

        # 2. Supercast/Substack-style: token as a path segment of the feed and the audio.
        path_audio = f"audio/{token}/ep2.m4a"
        os.makedirs(os.path.dirname(path_audio), exist_ok=True)
        if not os.path.exists(path_audio):
            subprocess.run(["cp", "audio/ep2.m4a", path_audio], check=True)
        write(f"feeds/{token}/path-token.rss", feed_xml(
            f"{SHOW} (subscriber {name.upper()})",
            f"{BASE}/feeds/{token}/path-token.rss", "ep2",
            f"{BASE}/{path_audio}", "smtf-ep2", "audio/ep2.m4a"))

        # 3. GUID is the tokenized audio link.
        guid_audio = f"{BASE}/audio/ep3.m4a?token={token}"
        write(f"feeds/{token}/guid-is-link.rss", feed_xml(
            f"{SHOW} (subscriber {name.upper()})",
            f"{BASE}/feeds/{token}/guid-is-link.rss", "ep3",
            guid_audio, guid_audio, "audio/ep3.m4a", is_permalink=True))

    write("index.html", index_html())


INDEX_CASES = [
    ("Public control", "A normal public feed. Its links should survive sharing.", "public"),
    ("Query token (Patreon style)", "The token is in the feed link and the audio link's query.", "query"),
    ("Path token (Supercast / Substack style)", "The token is a folder in the feed and audio links.", "path"),
    ("GUID is the link", "The episode GUID is the tokenized audio link.", "guid"),
]


def feed_links(case):
    if case == "public":
        url = f"{BASE}/feeds/public/show.rss"
        return [("Anyone", url)]
    links = []
    for name, token in SUBSCRIBERS.items():
        label = f"Subscriber {name.upper()}"
        if case == "query":
            links.append((label, f"{BASE}/feeds/subscriber-{name}/query-token.rss?auth={token}"))
        elif case == "path":
            links.append((label, f"{BASE}/feeds/{token}/path-token.rss"))
        else:
            links.append((label, f"{BASE}/feeds/{token}/guid-is-link.rss"))
    return links


def index_html():
    sections = []
    for title, note, case in INDEX_CASES:
        rows = "".join(
            f'''<li><span class="who">{escape(who)}</span>
<a href={quoteattr(url)}><code>{escape(url)}</code></a>
<button type="button" data-url={quoteattr(url)}>Copy</button></li>'''
            for who, url in feed_links(case))
        sections.append(f"<section><h2>{escape(title)}</h2><p>{escape(note)}</p><ul>{rows}</ul></section>")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test Feeds</title>
<style>
:root {{ --bg:#fbfaf6; --fg:#1d1d1b; --muted:#5b5b57; --card:#ffffff; --line:#dedbd2; --accent:#0a5fa8; --accent-fg:#ffffff; --done:#b85c00; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161614; --fg:#f1efe8; --muted:#b3b0a6; --card:#22221f; --line:#3a3934; --accent:#5aa9e6; --accent-fg:#0b1b29; --done:#f0a04b; }} }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:17px/1.45 -apple-system, system-ui, sans-serif; }}
main {{ max-width:720px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:1.6rem; margin:0 0 8px; }}
h2 {{ font-size:1.15rem; margin:0 0 4px; }}
p {{ margin:0 0 12px; color:var(--muted); }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; margin:16px 0; }}
ul {{ list-style:none; margin:0; padding:0; }}
li {{ display:grid; grid-template-columns:1fr auto; gap:6px 12px; padding:10px 0; border-top:1px solid var(--line); align-items:center; }}
li:first-child {{ border-top:0; }}
.who {{ grid-column:1 / -1; font-weight:600; }}
code {{ font:13px/1.35 ui-monospace, Menlo, monospace; overflow-wrap:anywhere; color:var(--muted); }}
li a {{ color:inherit; text-decoration-color:var(--line); }}
button {{ font:inherit; font-weight:600; min-width:88px; min-height:44px; border:0; border-radius:10px; background:var(--accent); color:var(--accent-fg); }}
button.copied {{ background:var(--done); }}
</style>
</head>
<body>
<main>
<h1>Spoken Margins test feeds</h1>
<p>Fake &ldquo;paid&rdquo; podcast feeds for testing link privacy. <strong>Every token is made up.</strong></p>
<p>Tap Copy next to a feed (or long-press its link and choose Copy Link), then in the app use Library &rarr; + &rarr; Link or Podcast &rarr; Paste. Copy a feed link, not this page&rsquo;s address: the page itself imports as an article.</p>
<p>After sharing a Margin from a private feed, the packet should not contain the subscriber tokens, which begin FAKEsubA or FAKEsubB. Each feed holds one short episode.</p>
{"".join(sections)}
<p>Source and notes: <a href="https://github.com/uncomposed/spoken-margins-test-feeds">github.com/uncomposed/spoken-margins-test-feeds</a></p>
</main>
<script>
document.querySelectorAll("button[data-url]").forEach(function (b) {{
  b.addEventListener("click", function () {{
    var done = function () {{ b.textContent = "Copied \u2713"; b.classList.add("copied");
      setTimeout(function () {{ b.textContent = "Copy"; b.classList.remove("copied"); }}, 2000); }};
    if (navigator.clipboard) {{ navigator.clipboard.writeText(b.dataset.url).then(done, function () {{ b.textContent = "Long-press the link"; }}); }}
    else {{ b.textContent = "Long-press the link"; }}
  }});
}});
</script>
</body>
</html>
'''


if __name__ == "__main__":
    main()
