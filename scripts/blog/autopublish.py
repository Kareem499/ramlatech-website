#!/usr/bin/env python3
"""Ramlatech AI blog writer.

Adds one AI-written post every INTERVAL_DAYS days (TOTAL_POSTS in all) as a
Markdown file in content/blog/, then rebuilds the blog. Posts you write in the
dashboard (/admin) are separate and don't affect this schedule.

- Topics come from scripts/blog/topics.json first, then Claude picks its own.
- Every third post (and any queued topic with "type": "comparison") is a
  comparison: Claude researches with web search, and only links that actually
  came back from those searches are kept as sources. Fewer than MIN_SOURCES
  verified sources means nothing is published.

Usage:
  python scripts/blog/autopublish.py            # write a post if one is due
  python scripts/blog/autopublish.py --force    # write one now
  python scripts/blog/autopublish.py --fake     # placeholder post, no API call (testing)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

HERE = Path(__file__).resolve().parent
BRIEF_FILE = HERE / "brief.md"
TOPICS_FILE = HERE / "topics.json"

START_DATE = dt.date(2026, 11, 21)
INTERVAL_DAYS = 2
TOTAL_POSTS = 365
COMPARISON_EVERY = 3        # every 3rd AI post is a comparison
MIN_WORDS = 700
MIN_SOURCES = 3
MAX_SEARCHES = 8
MODEL = os.environ.get("BLOG_MODEL") or "claude-opus-5-5"
CATEGORY_LABELS = [label for label, _, _ in build.CATEGORIES]

SUBMIT_TOOL = {
    "name": "submit_article",
    "description": "Submit the finished article. Call this exactly once, when the article is complete.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "At most 70 characters."},
            "slug": {"type": "string", "description": "lowercase-words-joined-by-hyphens, at most 60 characters."},
            "excerpt": {"type": "string", "description": "One or two sentences for the blog listing card."},
            "description": {"type": "string", "description": "SEO meta description, 140-155 characters."},
            "category": {"type": "string", "enum": CATEGORY_LABELS},
            "body_markdown": {"type": "string", "description": "The article body in Markdown, without the title."},
            "sources": {
                "type": "array",
                "description": "Pages from your web searches that support the facts in the article. Empty if you did not search.",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "url": {"type": "string"}},
                    "required": ["title", "url"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["title", "slug", "excerpt", "description", "category", "body_markdown", "sources"],
        "additionalProperties": False,
    },
}


# --------------------------------------------------------------------------- state
def ai_posts() -> list[dict]:
    out = []
    for f in build.CONTENT_DIR.glob("*.md"):
        meta, _ = build.split_front_matter(f.read_text(encoding="utf-8"))
        if meta.get("generated"):
            d = build.parse_date(meta.get("date"))
            if d:
                out.append({"title": str(meta.get("title", "")), "date": d, "file": f})
    return sorted(out, key=lambda p: p["date"])


def all_titles() -> list[str]:
    titles = []
    for f in sorted(build.CONTENT_DIR.glob("*.md")):
        meta, _ = build.split_front_matter(f.read_text(encoding="utf-8"))
        if meta.get("title"):
            titles.append(str(meta["title"]))
    return titles


def norm_url(u: str) -> str:
    u = u.strip().split("#", 1)[0]
    return u[:-1] if u.endswith("/") else u


# --------------------------------------------------------------------------- prompt
def build_prompt(today: dt.date, topic: dict | None, comparison: bool, titles: list[str], queue: list[dict]) -> tuple[str, str]:
    brief = BRIEF_FILE.read_text(encoding="utf-8")
    system = (
        "You write articles for the Ramlatech company blog. Follow the brief exactly.\n\n" + brief +
        "\n\n## How to deliver\n"
        "When the article is finished, call the submit_article tool exactly once.\n"
        "- body_markdown: 1,000-1,500 words of Markdown. Use ## and ### headings, short paragraphs, lists, "
        "and a Markdown table where a comparison helps. No H1 (the page shows the title). No images, no HTML.\n"
        f"- category: one of {', '.join(CATEGORY_LABELS)}.\n"
        "- Internal links: only the Ramlatech paths listed in the brief (root-relative, e.g. /services.html#ai)."
    )
    lines = [f"Today is {today.strftime('%B %-d, %Y')}."]
    if comparison:
        lines.append(
            "This is a COMPARISON post. Before writing, research it with web search: official product and pricing "
            "pages, documentation, and reputable independent sources. Then:\n"
            "- State facts about named companies, products or prices only when your search results support them, "
            "and link the supporting page inline the first time you use it.\n"
            f"- Say these facts are current as of {today.strftime('%B %Y')}, and that prices and features change.\n"
            "- Be fair and balanced: explain when each option is the better choice. No disparaging language.\n"
            "- If Ramlatech's own offering is one of the options (e.g. agency vs freelancers), say plainly that we "
            "are a software agency and give the honest case for the alternatives too.\n"
            "- Include a Markdown comparison table.\n"
            f"- List in `sources` at least {MIN_SOURCES} pages you actually found in your searches. Do not add a "
            "Sources heading to the body; the page adds it.\n"
            "- External links in the body must be pages from your searches; no other external links.")
        lines.append("Use the category Comparisons.")
    else:
        lines.append("Do not use external links. Set `sources` to an empty list.")
    if topic:
        lines.append(f'Write the article with this exact title: "{topic["title"]}".')
    elif comparison:
        lines.append("Choose a fresh comparison our readers would search for: either agency vs alternatives "
                     "(freelancers, in-house, hiring marketplaces, no-code) or a neutral tech/tool buyer's guide "
                     "(frameworks, platforms, cloud, e-commerce, AI tools).")
    else:
        lines.append("Choose a fresh, specific topic from the brief's topic areas; prefer the area used least "
                     "recently in the list below.")
    if titles:
        lines.append("Already on the blog (do not repeat or closely overlap):\n- " + "\n- ".join(titles[-400:]))
    reserved = [t["title"] for t in queue if not topic or t["title"] != topic["title"]]
    if reserved:
        lines.append("Reserved for future posts (do not write these now):\n- " + "\n- ".join(reserved))
    return system, "\n\n".join(lines)


# --------------------------------------------------------------------------- generation
def generate_with_claude(system: str, user: str, comparison: bool) -> tuple[dict, set[str]]:
    import anthropic

    client = anthropic.Anthropic()
    tools = [SUBMIT_TOOL]
    if comparison:
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": MAX_SEARCHES}, SUBMIT_TOOL]
    messages: list = [{"role": "user", "content": user}]
    found_urls: set[str] = set()

    for _ in range(8):  # continuations for pause_turn / a missing submit call
        try:
            response = client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=system,
                tools=tools,
                tool_choice={"type": "auto"},
                output_config={"effort": "high"},
                messages=messages,
            )
        except anthropic.AuthenticationError:
            raise SystemExit("ANTHROPIC_API_KEY is missing or invalid — add it as a GitHub Actions secret.")
        except anthropic.RateLimitError as e:
            raise SystemExit(f"Rate limited by the Claude API; will retry on the next run. ({e.message})")
        except anthropic.APIStatusError as e:
            raise SystemExit(f"Claude API error {e.status_code}: {e.message}")
        except anthropic.APIConnectionError:
            raise SystemExit("Could not reach the Claude API; will retry on the next run.")

        print(f"request id: {response._request_id}  model: {response.model}  stop: {response.stop_reason}  "
              f"tokens in/out: {response.usage.input_tokens}/{response.usage.output_tokens}")

        for block in response.content:
            if getattr(block, "type", "") == "web_search_tool_result" and isinstance(getattr(block, "content", None), list):
                for r in block.content:
                    if getattr(r, "url", None):
                        found_urls.add(norm_url(r.url))

        if response.stop_reason == "refusal":
            raise SystemExit("Claude declined this topic; nothing published. Edit scripts/blog/topics.json and re-run.")
        if response.stop_reason == "max_tokens":
            raise SystemExit("The response was cut off (max_tokens); nothing published. Will retry on the next run.")

        submit = next((b for b in response.content if getattr(b, "type", "") == "tool_use" and b.name == "submit_article"), None)
        if submit is not None:
            return dict(submit.input), found_urls

        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "pause_turn":
            messages.append({"role": "user", "content": "Now call submit_article with the complete article."})
    raise SystemExit("Claude did not submit an article; nothing published. Will retry on the next run.")


def fake_article(topic: dict | None, comparison: bool) -> tuple[dict, set[str]]:
    title = topic["title"] if topic else "A sample article for testing the layout"
    para = ("This is placeholder text used to test the page template. It never reaches the live site because it "
            "only appears when the script runs with --fake. ") * 3
    body = (f"Opening paragraph that frames the problem.\n\n## Why this matters\n\n{para}\n\n{para}\n\n"
            "## Side by side\n\n| | Option A | Option B |\n|---|---|---|\n| Cost | Lower | Higher |\n| Speed | Faster | Slower |\n\n"
            "## A practical checklist\n\n- Define the outcome.\n- Scope the smallest version.\n- Plan how to measure it.\n\n"
            "See our [custom software](/services.html#custom) service, [a verified source](https://example.com/pricing) "
            "and [an unverified link that gets removed](https://made-up.example.org/page).\n\n"
            + ("\n\n".join([para] * 12)))
    sources = [{"title": f"Source {i}", "url": f"https://example.com/{p}"} for i, p in enumerate(["pricing", "docs", "about", "fake-unfound"], 1)]
    found = {"https://example.com/pricing", "https://example.com/docs", "https://example.com/about"}
    cat = "Comparisons" if comparison else (topic or {}).get("category", "Startups")
    return {"title": title, "slug": build.re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60],
            "excerpt": "A placeholder excerpt used to test how the listing card looks.",
            "description": "Placeholder description used to test the Ramlatech blog template; it is roughly one hundred and fifty characters long here.",
            "category": cat, "body_markdown": body, "sources": sources if comparison else []}, (found if comparison else set())


def finalize(raw: dict, found: set[str], topic: dict | None, comparison: bool, today: dt.date) -> tuple[str, str]:
    """Validate the article and return (slug, markdown file text)."""
    body = raw["body_markdown"].strip()
    body = re.sub(r"^#\s+.*\n+", "", body)  # drop a stray H1

    # keep only external links that came back from web search
    def check_link(m: re.Match) -> str:
        text, url = m.group(1), m.group(2)
        if url.startswith("/") or norm_url(url) in found:
            return m.group(0)
        return text
    body = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)", check_link, body)

    words = len(re.sub(r"[#*_`|>\-\[\]()]", " ", body).split())
    if words < MIN_WORDS:
        raise SystemExit(f"Article too short ({words} words); nothing published.")

    sources = []
    if comparison:
        seen = set()
        for s in raw.get("sources", []):
            u = norm_url(str(s.get("url", "")))
            if u in found and u not in seen:
                seen.add(u)
                sources.append((str(s.get("title") or u).strip(), s["url"].strip()))
        if len(sources) < MIN_SOURCES:
            raise SystemExit(f"Only {len(sources)} verified sources (need {MIN_SOURCES}); nothing published. Will retry next run.")
        body += (f"\n\n## Sources\n\n*Researched in {today.strftime('%B %Y')}. Prices and features change — "
                 "check each provider's site for current details.*\n\n" +
                 "\n".join(f"- [{t.replace(']', '')}]({u})" for t, u in sources))

    title = re.sub(r"\s+", " ", topic["title"] if topic else raw["title"]).strip()[:120]
    if title.lower() in {t.lower() for t in all_titles()}:
        raise SystemExit(f'"{title}" is already on the blog; nothing published.')
    slug = re.sub(r"[^a-z0-9]+", "-", (raw.get("slug") or title).lower()).strip("-")[:60].strip("-") or "post"
    base, n = slug, 2
    while (build.CONTENT_DIR / f"{slug}.md").exists() or slug in {"index", "feed", "page", "category"}:
        slug, n = f"{base}-{n}", n + 1

    category = "Comparisons" if comparison else (raw["category"] if raw["category"] in CATEGORY_LABELS else "Strategy")
    desc = re.sub(r"\s+", " ", raw["description"]).strip()
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "…"
    meta = {
        "title": title,
        "date": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "draft": False,
        "category": category,
        "author": build.DEFAULT_AUTHOR,
        "excerpt": re.sub(r"\s+", " ", raw["excerpt"]).strip()[:300],
        "description": desc,
        "generated": True,
    }
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    return slug, f"---\n{front}\n---\n\n{body}\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="write a post now even if one is not due")
    ap.add_argument("--fake", action="store_true", help="placeholder article, no API call (testing)")
    ap.add_argument("--comparison", action="store_true", help="with --fake/--force: make it a comparison post")
    ap.add_argument("--date", help="pretend today is YYYY-MM-DD (testing)")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date()
    done = ai_posts()
    if len(done) >= TOTAL_POSTS:
        print(f"All {TOTAL_POSTS} AI posts are published. Nothing to do.")
        return 0
    if not args.force:
        if today < START_DATE:
            print(f"AI schedule starts {START_DATE}; nothing to do.")
            return 0
        if done:
            gap = (today - done[-1]["date"].date()).days
            if gap < INTERVAL_DAYS:
                print(f"Last AI post was {gap} day(s) ago; next one is due in {INTERVAL_DAYS - gap} day(s).")
                return 0

    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8")) if TOPICS_FILE.exists() else {"queue": []}
    existing = {t.lower() for t in all_titles()}
    queue = [t for t in topics.get("queue", []) if t["title"].lower() not in existing]
    topic = queue[0] if queue else None
    comparison = args.comparison or (topic.get("type") == "comparison" if topic else (len(done) % COMPARISON_EVERY == COMPARISON_EVERY - 1))

    system, user = build_prompt(today, topic, comparison, all_titles(), queue)
    raw, found = fake_article(topic, comparison) if args.fake else generate_with_claude(system, user, comparison)
    slug, text = finalize(raw, found, topic, comparison, today)
    if args.fake and args.date:  # date the placeholder by the simulated day
        text = re.sub(r"^date: .*$", f"date: '{today.isoformat()}T06:00:00Z'", text, count=1, flags=re.M)

    build.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (build.CONTENT_DIR / f"{slug}.md").write_text(text, encoding="utf-8")
    if topic:
        topics["queue"] = [t for t in topics.get("queue", []) if t["title"] != topic["title"]]
        TOPICS_FILE.write_text(json.dumps(topics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    title = re.search(r"^title: (.*)$", text, re.M).group(1).strip("'\"")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"generated=true\ntitle={title}\n")
    kind = "comparison" if comparison else "post"
    print(f"Wrote AI {kind} {len(done) + 1}/{TOTAL_POSTS}: {title} -> content/blog/{slug}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
