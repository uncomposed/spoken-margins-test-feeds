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


if __name__ == "__main__":
    main()
