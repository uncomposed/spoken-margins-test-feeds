# Spoken Margins test feeds

Fake "paid" podcast feeds for testing whether [Spoken Margins](https://github.com/uncomposed/spoken-margins-native) keeps subscriber secrets out of shared packets and exports (issues #168 and #177).

**Every token here is made up.** They start with `FAKEsub` so they are easy to search for. Nothing here grants access to anything.

## Feeds

Paste a feed link into the app's "add a link" field. Each feed holds one episode, so the app picks it without asking.

| Case | What it copies | Subscriber A | Subscriber B |
|---|---|---|---|
| Public control | A normal public feed. Links should survive sharing unchanged. | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/public/show.rss` | same |
| Query token | Patreon style: token in the feed's and the audio link's query | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/subscriber-a/query-token.rss?auth=FAKEsubA7f3a9c2e41b8d6a5c4b3e2f1a0d9c8b7` | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/subscriber-b/query-token.rss?auth=FAKEsubB1e2d3c4b5a69788776655443322110ff` |
| Path token | Supercast / Substack style: token as a folder in the feed and audio links | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/FAKEsubA7f3a9c2e41b8d6a5c4b3e2f1a0d9c8b7/path-token.rss` | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/FAKEsubB1e2d3c4b5a69788776655443322110ff/path-token.rss` |
| GUID is the link | The episode GUID is the tokenized audio link | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/FAKEsubA7f3a9c2e41b8d6a5c4b3e2f1a0d9c8b7/guid-is-link.rss` | `https://uncomposed.github.io/spoken-margins-test-feeds/feeds/FAKEsubB1e2d3c4b5a69788776655443322110ff/guid-is-link.rss` |

Subscribers A and B see the same episodes with the same GUIDs (except the GUID-is-link case), but different tokens. That is the setup a real paid show has, and it is what #177 needs to match Margins between two subscribers.

## Checking a packet

A `.spokenmargins` packet is a zip file. After sharing from one of the private feeds:

```bash
unzip -p shared.spokenmargins | grep -c FAKEsub
```

A count of 0 means no token left the device.

## What this does not show

- Known private hosts (Patreon, Supercast and others). The app drops those by host name, and these feeds live on github.io.
- Redirects, expiring links or dynamic ad insertion. GitHub Pages serves the same file for every request and ignores query strings.
- Whether a real paid feed's GUIDs are stable. Only a real feed can show that.

## Rebuilding

`python3 build.py` regenerates the feeds, and generates the audio with macOS `say` if it's missing. The audio is synthetic speech written for this repo.
