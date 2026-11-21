#!/usr/bin/env python3
"""Build the Ramlatech blog from content/blog/*.md.

Each Markdown file is one post (YAML front matter + Markdown body). A post is
published when `draft` is false and its `date` has passed. Running this script
(re)generates, deterministically:

  blog.html                         listing page 1 (between the BLOG-LISTING markers)
  blog/page/<n>.html                listing pages 2+
  blog/category/<cat>.html (+/<n>)  category listings
  blog/<slug>.html                  one page per published post
  blog/index.html                   redirect to /blog.html
  blog/feed.xml                     RSS (latest 30)
  sitemap.xml                       blog entries between BLOG-AUTO markers

Usage:  python scripts/blog/build.py [--now 2026-12-01T09:00:00Z]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import re
import shutil
import sys
from dataclasses import dataclass, field
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content" / "blog"
OUT_DIR = ROOT / "blog"
TOPICS_FILE = Path(__file__).resolve().parent / "topics.json"
SITE = "https://ramlatech.com"
PER_PAGE = 12
FEED_SIZE = 30
DEFAULT_AUTHOR = "Ramlatech Team"

# label, url slug, colour
CATEGORIES = [
    ("Startups", "startups", "teal"),
    ("AI & Automation", "ai-automation", "gold"),
    ("Development", "development", "teal"),
    ("Security", "security", "navy"),
    ("Strategy", "strategy", "olive"),
    ("Budgeting", "budgeting", "navy"),
    ("Comparisons", "comparisons", "gold"),
]
CAT_SLUG = {label: slug for label, slug, _ in CATEGORIES}
CAT_COLOUR = {label: colour for label, _, colour in CATEGORIES}


# --------------------------------------------------------------------------- model
@dataclass
class Post:
    slug: str
    title: str
    date: dt.datetime
    category: str
    excerpt: str
    author: str
    description: str
    cover: str
    body_html: str
    words: int
    generated: bool = False
    draft: bool = False
    tags: list = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"/blog/{self.slug}.html"

    @property
    def minutes(self) -> int:
        return max(1, round(self.words / 230))

    @property
    def day(self) -> str:
        return self.date.date().isoformat()

    @property
    def nice_date(self) -> str:
        return self.date.strftime("%b %-d, %Y")

    @property
    def colour(self) -> str:
        return CAT_COLOUR.get(self.category, "teal")


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def parse_date(value) -> dt.datetime | None:
    """Accepts datetime/date objects or ISO strings (with Z, offset, or none = UTC)."""
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        d = value
    elif isinstance(value, dt.date):
        d = dt.datetime.combine(value, dt.time(0, 0))
    else:
        s = str(value).strip().replace("Z", "+00:00")
        try:
            d = dt.datetime.fromisoformat(s)
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


# --------------------------------------------------------------------------- sanitising
class Sanitizer(HTMLParser):
    """Allow-list HTML cleaner for post bodies (Markdown output)."""
    KEEP = {"h2", "h3", "h4", "p", "ul", "ol", "li", "blockquote", "strong", "em", "a", "code", "pre",
            "hr", "br", "img", "table", "thead", "tbody", "tr", "th", "td", "del", "sup", "sub"}
    DROP = {"script", "style", "iframe", "object", "embed", "svg", "noscript", "template", "form", "button", "input", "select", "textarea"}
    VOID = {"hr", "br", "img"}
    REMAP = {"h1": "h2", "b": "strong", "i": "em", "h5": "h4", "h6": "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[str] = []
        self.skip = 0

    @staticmethod
    def safe_url(u: str, images: bool = False) -> str | None:
        u = (u or "").strip()
        if re.match(r"^https?://", u, re.I):
            return u
        if u.startswith("/") and not u.startswith("//"):
            return u
        if not images and u.startswith("#"):
            return u
        return None

    def handle_starttag(self, tag, attrs):
        tag = self.REMAP.get(tag, tag)
        if tag in self.DROP:
            self.skip += 1
            return
        if self.skip:
            return
        a = dict(attrs)
        if tag not in self.KEEP:
            if tag not in {"meta", "link", "source", "wbr", "input"}:
                self.stack.append("")
            return
        if tag == "a":
            href = self.safe_url(a.get("href", ""))
            if not href:
                self.stack.append("")
                return
            external = href.startswith("http") and "ramlatech.com" not in href
            extra = ' target="_blank" rel="noopener noreferrer"' if external else ""
            self.out.append(f'<a href="{esc(href)}"{extra}>')
            self.stack.append("a")
            return
        if tag == "img":
            src = self.safe_url(a.get("src", ""), images=True)
            if src:
                self.out.append(f'<img src="{esc(src)}" alt="{esc(a.get("alt", ""))}" loading="lazy" decoding="async" />')
            return
        if tag in self.VOID:
            self.out.append(f"<{tag} />")
            return
        if tag in {"th", "td"} and a.get("align") in {"left", "right", "center"}:
            self.out.append(f'<{tag} style="text-align:{a["align"]}">')
        else:
            self.out.append(f"<{tag}>")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = self.REMAP.get(tag, tag)
        if tag in self.DROP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag in self.VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] in (tag, ""):
                t = self.stack.pop(i)
                if t:
                    self.out.append(f"</{t}>")
                return

    def handle_data(self, data):
        if not self.skip:
            self.out.append(esc(data))

    def result(self) -> str:
        while self.stack:
            t = self.stack.pop()
            if t:
                self.out.append(f"</{t}>")
        return "".join(self.out).strip()


def render_markdown(body: str) -> str:
    raw = markdown.markdown(body or "", extensions=["extra", "sane_lists"], output_format="html")
    s = Sanitizer()
    s.feed(raw)
    s.close()
    return s.result()


# --------------------------------------------------------------------------- loading
def split_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return (meta if isinstance(meta, dict) else {}), m.group(2)


def load_posts() -> list[Post]:
    posts = []
    for f in sorted(CONTENT_DIR.glob("*.md")):
        meta, body = split_front_matter(f.read_text(encoding="utf-8"))
        title = str(meta.get("title") or "").strip()
        date = parse_date(meta.get("date"))
        if not title or not date:
            print(f"warning: skipping {f.name}: needs a title and a date", file=sys.stderr)
            continue
        slug = re.sub(r"[^a-z0-9-]+", "-", f.stem.lower()).strip("-")
        body_html = render_markdown(body)
        words = len(re.sub(r"<[^>]+>", " ", body_html).split())
        category = meta.get("category") if meta.get("category") in CAT_COLOUR else "Strategy"
        excerpt = re.sub(r"\s+", " ", str(meta.get("excerpt") or "")).strip()
        if not excerpt:
            text = re.sub(r"<[^>]+>", " ", body_html)
            excerpt = (" ".join(text.split()[:30]) + "…") if text.strip() else ""
        desc = re.sub(r"\s+", " ", str(meta.get("description") or excerpt)).strip()[:160]
        posts.append(Post(slug=slug, title=title, date=date, category=category, excerpt=excerpt,
                          author=str(meta.get("author") or DEFAULT_AUTHOR).strip(), description=desc,
                          cover=str(meta.get("cover") or "").strip(), body_html=body_html, words=words,
                          generated=bool(meta.get("generated")), draft=bool(meta.get("draft"))))
    return posts


# --------------------------------------------------------------------------- page chrome
def absolutize(fragment: str) -> str:
    return re.sub(r'(href|src)="(?!https?:|mailto:|tel:|#|/|data:)([^"]*)"', r'\1="/\2"', fragment)


def blog_template() -> str:
    return (ROOT / "blog.html").read_text(encoding="utf-8")


def chrome(template: str) -> tuple[str, str]:
    nav = re.search(r'<nav id="main-nav">.*?</nav>', template, re.S).group(0)
    footer = re.search(r"<footer>.*?</footer>", template, re.S).group(0)
    footer = footer.replace("nl-footer-email-blog", "nl-footer-email-post")
    return absolutize(nav), absolutize(footer)


LISTING_CSS = """<style>
.bl-chips{display:flex;flex-wrap:wrap;gap:.6rem;margin-bottom:2.25rem}
.bl-chips a{font-family:var(--font-display);font-size:.88rem;font-weight:500;color:var(--navy);border:1px solid rgba(14,31,56,.15);border-radius:100px;padding:.45rem 1.05rem;transition:all .2s}
.bl-chips a:hover{border-color:var(--teal);color:var(--teal)}
.bl-chips a.on{background:var(--teal);border-color:var(--teal);color:#fff}
.bl-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1.75rem}
.bcard{display:flex;flex-direction:column;background:var(--white);border-radius:16px;overflow:hidden;border:1px solid rgba(14,31,56,.08);box-shadow:0 4px 24px rgba(14,31,56,.06);transition:transform .3s var(--ease),box-shadow .3s var(--ease);color:inherit}
a.bcard:hover{transform:translateY(-5px);box-shadow:0 16px 44px rgba(14,31,56,.12)}
.bcard-cover{position:relative;aspect-ratio:16/8.5;display:flex;align-items:flex-start;padding:1.25rem;overflow:hidden;background-size:cover;background-position:center}
.bcard-cover::before{content:'';position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.12) 1.2px,transparent 1.2px);background-size:22px 22px;opacity:.7}
.bcard-cover.has-img::before{background:linear-gradient(160deg,rgba(10,28,51,.35),rgba(10,28,51,.8));opacity:1}
.bcard-cover.teal{background-image:linear-gradient(135deg,#0B8A8A,#0E1F38)}
.bcard-cover.gold{background-image:linear-gradient(135deg,#C4882B,#0E1F38)}
.bcard-cover.navy{background-image:linear-gradient(135deg,#1d3a63,#0a1428)}
.bcard-cover.olive{background-image:linear-gradient(135deg,#4B7A45,#0E1F38)}
.bcard-cover.has-img{background-color:#0E1F38}
.bcard-cover-title{position:relative;z-index:1;font-family:var(--font-display);font-weight:700;font-size:1.05rem;line-height:1.3;color:#fff;max-width:85%;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.bcard-mark{position:absolute;z-index:1;right:1rem;bottom:.85rem;font-family:var(--font-display);font-weight:700;font-size:.8rem;color:#fff;letter-spacing:-.01em}
.bcard-mark b{color:var(--gold);font-weight:700}
.bcard-body{padding:1.35rem 1.4rem 1.5rem;display:flex;flex-direction:column;flex:1}
.bcard-cat{font-family:var(--font-display);font-size:.72rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--teal);margin-bottom:.6rem}
.bcard-cat.gold{color:var(--gold)}.bcard-cat.navy{color:var(--navy)}.bcard-cat.olive{color:var(--olive)}
.bcard h3{font-family:var(--font-display);font-size:1.12rem;font-weight:700;color:var(--navy);line-height:1.35;margin-bottom:.55rem}
.bcard p{font-size:.9rem;color:var(--stone);line-height:1.6;margin-bottom:1rem;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.bcard-meta{font-size:.8rem;color:var(--stone);margin-top:auto}
.bcard-link{font-family:var(--font-display);font-size:.88rem;font-weight:600;color:var(--teal);margin-top:.9rem}
.bcard-soon{font-family:var(--font-display);font-size:.78rem;color:var(--stone);margin-top:auto}
.bl-pager{display:flex;justify-content:center;align-items:center;gap:1.25rem;margin-top:3rem;font-family:var(--font-display);font-size:.9rem;color:var(--stone)}
.bl-pager a{font-weight:600;color:var(--teal);border:1px solid rgba(11,138,138,.3);border-radius:100px;padding:.45rem 1.1rem}
.bl-pager a:hover{background:var(--teal);color:#fff}
.bl-empty{color:var(--stone);margin-bottom:2rem}
@media(max-width:900px){.bl-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.bl-grid{grid-template-columns:1fr}}
</style>"""


def listing_url(cat_slug: str | None, page: int) -> str:
    if cat_slug:
        return f"/blog/category/{cat_slug}.html" if page == 1 else f"/blog/category/{cat_slug}/{page}.html"
    return "/blog.html" if page == 1 else f"/blog/page/{page}.html"


def card(p: Post) -> str:
    cover_style = f' style="background-image:url(\'{esc(p.cover)}\')"' if p.cover else ""
    cover_cls = f"bcard-cover has-img" if p.cover else f"bcard-cover {p.colour}"
    return f"""
      <a class="bcard" href="{p.url}">
        <div class="{cover_cls}"{cover_style}>
          <span class="bcard-cover-title">{esc(p.title)}</span>
          <span class="bcard-mark" aria-hidden="true">Ramla<b>tech</b></span>
        </div>
        <div class="bcard-body">
          <div class="bcard-cat {p.colour}">{esc(p.category)}</div>
          <h3>{esc(p.title)}</h3>
          <p>{esc(p.excerpt)}</p>
          <div class="bcard-meta">{esc(p.author)} · {p.nice_date} · {p.minutes} min read</div>
          <span class="bcard-link">Read article →</span>
        </div>
      </a>"""


def coming_soon_card(t: dict) -> str:
    cat = t.get("category") if t.get("category") in CAT_COLOUR else "Strategy"
    colour = CAT_COLOUR[cat]
    return f"""
      <div class="bcard">
        <div class="bcard-cover {colour}">
          <span class="bcard-cover-title">{esc(t['title'])}</span>
          <span class="bcard-mark" aria-hidden="true">Ramla<b>tech</b></span>
        </div>
        <div class="bcard-body">
          <div class="bcard-cat {colour}">{esc(cat)}</div>
          <h3>{esc(t['title'])}</h3>
          <div class="bcard-soon">Coming soon</div>
        </div>
      </div>"""


def listing_region(posts: list[Post], all_posts: list[Post], cat_slug: str | None, page: int, pages: int) -> str:
    used = [label for label, _, _ in CATEGORIES if any(p.category == label for p in all_posts)]
    chips = [f'<a href="/blog.html"{" class=\"on\"" if cat_slug is None else ""}>All posts</a>']
    for label in used:
        s = CAT_SLUG[label]
        chips.append(f'<a href="{listing_url(s, 1)}"{" class=\"on\"" if s == cat_slug else ""}>{esc(label)}</a>')
    if all_posts:
        cards = "".join(card(p) for p in posts)
        empty = ""
    else:
        queue = json.loads(TOPICS_FILE.read_text(encoding="utf-8")).get("queue", []) if TOPICS_FILE.exists() else []
        cards = "".join(coming_soon_card(t) for t in queue[:3])
        empty = '<p class="bl-empty">Our first articles are on their way.</p>'
    pager = ""
    if pages > 1:
        prev = f'<a href="{listing_url(cat_slug, page - 1)}">← Previous</a>' if page > 1 else ""
        nxt = f'<a href="{listing_url(cat_slug, page + 1)}">Next →</a>' if page < pages else ""
        pager = f'<div class="bl-pager">{prev}<span>Page {page} / {pages}</span>{nxt}</div>'
    chips_html = f'<div class="bl-chips" role="navigation" aria-label="Blog categories">{"".join(chips)}</div>' if all_posts else ""
    return f"""<!-- Generated by scripts/blog/build.py — edit posts in /admin, not here -->
{LISTING_CSS}
<section class="section-pad" style="background:var(--pearl);">
  <div class="container">
    {chips_html}
    {empty}
    <div class="bl-grid">{cards}
    </div>
    {pager}
  </div>
</section>
"""


def fill_listing(template: str, region: str) -> str:
    pat = re.compile(r"(<!-- BLOG-LISTING:START -->)(.*?)(<!-- BLOG-LISTING:END -->)", re.S)
    if not pat.search(template):
        raise SystemExit("blog.html is missing the BLOG-LISTING markers")
    return pat.sub(lambda m: m.group(1) + "\n" + region + m.group(3), template, count=1)


def subpage(text: str, *, url: str, title: str, index: bool) -> str:
    """Turn a filled blog.html into a page that lives under /blog/."""
    text = absolutize(text)
    text = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, count=1, flags=re.S)
    text = re.sub(r'<link rel="canonical" href="[^"]*" />', f'<link rel="canonical" href="{SITE}{url}" />', text, count=1)
    text = re.sub(r'<meta property="og:url" content="[^"]*" />', f'<meta property="og:url" content="{SITE}{url}" />', text, count=1)
    text = re.sub(r'<meta property="og:title" content="[^"]*" />', f'<meta property="og:title" content="{esc(title)}" />', text, count=1)
    text = re.sub(r'\n<link rel="alternate" hreflang="[^"]*" href="[^"]*" />', "", text)
    if not index:
        text = re.sub(r'<meta name="robots" content="[^"]*" />', '<meta name="robots" content="noindex, follow" />', text, count=1)
    return text


# --------------------------------------------------------------------------- post page
POST_CSS = """<style>
.post-hero{background:linear-gradient(150deg,#0a1c33 0%,#0E1F38 60%,#0d2840 100%);padding:10rem 0 4.5rem}
.post-hero .wrap,.post-main .wrap{max-width:760px;margin:0 auto;padding:0 5%}
.crumbs{font-family:var(--font-mono);font-size:.78rem;color:rgba(250,248,244,.55);margin-bottom:1.5rem}
.crumbs a{color:rgba(250,248,244,.8)}.crumbs a:hover{color:var(--gold)}
.post-cat{font-family:var(--font-display);font-size:.75rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:#3ecfcf}
.post-cat.gold{color:var(--gold)}.post-cat.navy{color:#9fb3cf}.post-cat.olive{color:#8fc086}
.post-hero h1{font-family:var(--font-display);font-size:clamp(1.9rem,4vw,2.9rem);font-weight:700;color:var(--pearl);letter-spacing:-.03em;line-height:1.12;margin:.75rem 0 1.25rem}
.post-hero .meta{font-size:.88rem;color:rgba(250,248,244,.65)}
.post-main{background:var(--pearl);padding:3.5rem 0 5rem}
.post-cover{width:100%;height:auto;border-radius:16px;margin-bottom:2.5rem;display:block}
.article{font-size:1.06rem;line-height:1.8;color:var(--ink)}
.article h2{font-family:var(--font-display);font-size:1.6rem;font-weight:700;color:var(--navy);letter-spacing:-.02em;line-height:1.25;margin:2.6rem 0 1rem}
.article h3{font-family:var(--font-display);font-size:1.2rem;font-weight:600;color:var(--navy);margin:2rem 0 .75rem}
.article h4{font-family:var(--font-display);font-size:1.05rem;font-weight:600;color:var(--navy);margin:1.5rem 0 .5rem}
.article p{margin:0 0 1.25rem}
.article ul,.article ol{margin:0 0 1.4rem 1.4rem;padding:0}.article ul{list-style:disc}.article ol{list-style:decimal}
.article li{margin:.4rem 0}
.article a{color:var(--teal);text-decoration:underline;text-underline-offset:3px}.article a:hover{color:var(--navy)}
.article blockquote{border-left:3px solid var(--gold);padding:.25rem 0 .25rem 1.25rem;margin:1.75rem 0;color:var(--stone);font-style:italic}
.article code{font-family:var(--font-mono);font-size:.9em;background:rgba(14,31,56,.06);padding:.1em .35em;border-radius:4px}
.article pre{background:var(--navy);color:#e8eef6;padding:1.1rem 1.25rem;border-radius:12px;overflow-x:auto;margin:0 0 1.5rem}
.article pre code{background:none;padding:0;color:inherit}
.article img{max-width:100%;height:auto;border-radius:12px;margin:1rem 0}
.article hr{border:0;border-top:1px solid rgba(14,31,56,.12);margin:2.5rem 0}
.article table{width:100%;border-collapse:collapse;margin:0 0 1.75rem;font-size:.95rem;display:block;overflow-x:auto}
.article th,.article td{border:1px solid rgba(14,31,56,.12);padding:.6rem .8rem;text-align:left;vertical-align:top}
.article th{background:rgba(14,31,56,.05);font-family:var(--font-display);font-weight:600;color:var(--navy)}
.post-cta{margin-top:3.5rem;background:var(--navy);border-radius:18px;padding:2.25rem;color:var(--pearl)}
.post-cta h2{font-family:var(--font-display);font-size:1.4rem;font-weight:700;margin-bottom:.6rem;color:var(--pearl)}
.post-cta p{color:rgba(250,248,244,.7);margin-bottom:1.25rem;line-height:1.7}
.more-posts{margin-top:3.5rem}
.more-posts h2{font-family:var(--font-display);font-size:1.1rem;font-weight:700;color:var(--navy);margin-bottom:1rem}
.more-posts a{display:block;padding:.9rem 0;border-top:1px solid rgba(14,31,56,.08);font-family:var(--font-display);font-weight:600;color:var(--navy)}
.more-posts a:hover{color:var(--teal)}
.more-posts span{display:block;font-family:var(--font-mono);font-size:.72rem;font-weight:400;color:var(--stone);margin-top:.2rem}
</style>"""

HEAD_COMMON = """<link rel="icon" type="image/png" href="/assets/mark-navy.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Cairo:wght@400;500;600;700&display=swap" />
<link rel="dns-prefetch" href="https://www.googletagmanager.com" />
<link rel="stylesheet" href="/main.css" />
<link rel="alternate" type="application/rss+xml" title="Ramlatech Blog" href="/blog/feed.xml" />
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KXS97MYKLJ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-KXS97MYKLJ');</script>"""


def abs_url(u: str) -> str:
    return u if u.startswith("http") else SITE + u


def render_post(p: Post, published: list[Post], nav: str, footer: str) -> str:
    url = SITE + p.url
    image = abs_url(p.cover) if p.cover else f"{SITE}/assets/og-card.jpg"
    others = [o for o in published if o.slug != p.slug][:3]
    more = ""
    if others:
        links = "".join(f'<a href="{o.url}">{esc(o.title)}<span>{o.nice_date} · {o.minutes} min read</span></a>' for o in others)
        more = f'<div class="more-posts"><h2>More from the blog</h2>{links}<a href="/blog.html">All articles →</a></div>'
    cat_url = listing_url(CAT_SLUG.get(p.category), 1)
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": p.title, "description": p.description,
         "datePublished": p.date.isoformat().replace("+00:00", "Z"), "url": url, "mainEntityOfPage": url,
         "image": image, "wordCount": p.words, "articleSection": p.category,
         "author": {"@type": "Organization" if p.author == DEFAULT_AUTHOR else "Person", "name": p.author},
         "publisher": {"@type": "Organization", "name": "Ramlatech", "url": SITE + "/",
                       "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo-navy.png"}}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE}/blog.html"},
            {"@type": "ListItem", "position": 3, "name": p.category, "item": SITE + cat_url},
            {"@type": "ListItem", "position": 4, "name": p.title, "item": url}]}]}
    cover = f'<img class="post-cover" src="{esc(p.cover)}" alt="" />' if p.cover else ""
    title = f"{p.title} | Ramlatech Blog"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{esc(title)}</title>
<meta name="description" content="{esc(p.description)}" />
<meta name="author" content="{esc(p.author)}" />
<meta name="robots" content="index, follow" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{url}" />
<meta property="og:title" content="{esc(p.title)}" />
<meta property="og:description" content="{esc(p.description)}" />
<meta property="og:image" content="{esc(image)}" />
<meta property="og:site_name" content="Ramlatech" />
<meta property="article:published_time" content="{p.date.isoformat().replace('+00:00', 'Z')}" />
<meta property="article:section" content="{esc(p.category)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@ramlatech" />
<meta name="twitter:title" content="{esc(p.title)}" />
<meta name="twitter:description" content="{esc(p.description)}" />
<meta name="twitter:image" content="{esc(image)}" />
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=2)}
</script>
{HEAD_COMMON}
{POST_CSS}
</head>
<body>
{nav}
<header class="post-hero">
  <div class="wrap">
    <div class="crumbs"><a href="/index.html">Home</a> / <a href="/blog.html">Blog</a> / <a href="{cat_url}">{esc(p.category)}</a></div>
    <div class="post-cat {p.colour}">{esc(p.category)}</div>
    <h1>{esc(p.title)}</h1>
    <div class="meta">{esc(p.author)} · {p.nice_date} · {p.minutes} min read</div>
  </div>
</header>
<main class="post-main">
  <div class="wrap">
    {cover}
    <article class="article">
{p.body_html}
    </article>
    <div class="post-cta">
      <h2>Planning something similar?</h2>
      <p>Talk it through with our team — a free 30-minute call, no pitch, just an honest view of what it would take.</p>
      <a href="/contact.html#book" class="btn btn-primary">Book a free consultation →</a>
    </div>
    {more}
  </div>
</main>
{footer}
<script src="/main.js" defer></script>
<script src="https://groot.mailerlite.com/js/w/webforms.min.js?v95037e5bac78f29ed026832ca21a7c7b" type="text/javascript" defer></script>
<script src="/lang.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------- feed + sitemap
def render_feed(published: list[Post]) -> str:
    items = []
    for p in published[:FEED_SIZE]:
        url = SITE + p.url
        items.append(f"""  <item>
    <title>{esc(p.title)}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{format_datetime(p.date)}</pubDate>
    <category>{esc(p.category)}</category>
    <description>{esc(p.excerpt)}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Ramlatech Blog</title>
  <link>{SITE}/blog.html</link>
  <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml" />
  <description>Practical guides on software, AI and building great products from Ramlatech.</description>
  <language>en</language>
{chr(10).join(items)}
</channel>
</rss>
"""


def update_sitemap(published: list[Post]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    entries = []
    for label, slug, _ in CATEGORIES:
        cat_posts = [p for p in published if p.category == label]
        if cat_posts:
            entries.append((SITE + listing_url(slug, 1), cat_posts[0].day, "weekly", "0.5"))
    entries += [(SITE + p.url, p.day, "yearly", "0.6") for p in published]
    block = "".join(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lm}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>\n"
                    for loc, lm, cf, pr in entries)
    region = f"  <!-- BLOG-AUTO:START -->\n{block}  <!-- BLOG-AUTO:END -->\n"
    pat = re.compile(r"  <!-- BLOG-AUTO:START -->\n.*?  <!-- BLOG-AUTO:END -->\n", re.S)
    text = pat.sub(lambda m: region, text) if pat.search(text) else text.replace("</urlset>", region + "</urlset>")
    if published:  # blog listing changes whenever the newest post changes
        text = re.sub(rf"(<loc>{re.escape(SITE)}/blog\.html</loc>\s*<lastmod>)[^<]*", rf"\g<1>{published[0].day}", text)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- build
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(now: dt.datetime) -> list[Post]:
    posts = load_posts()
    published = sorted((p for p in posts if not p.draft and p.date <= now), key=lambda p: (p.date, p.slug), reverse=True)
    template = blog_template()
    nav, footer = chrome(template)

    # fresh output folder (keeps blog/ purely generated)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # listing pages: all posts, then each category
    groups = [(None, "Blog", published)] + [
        (slug, label, [p for p in published if p.category == label]) for label, slug, _ in CATEGORIES]
    for cat_slug, label, items in groups:
        if cat_slug and not items:
            continue
        pages = max(1, math.ceil(len(items) / PER_PAGE))
        for page in range(1, pages + 1):
            chunk = items[(page - 1) * PER_PAGE: page * PER_PAGE]
            filled = fill_listing(template, listing_region(chunk, published, cat_slug, page, pages))
            url = listing_url(cat_slug, page)
            if url == "/blog.html":
                write(ROOT / "blog.html", filled)
                continue
            title = (f"{label} articles" if cat_slug else "Blog") + (f" — page {page}" if page > 1 else "") + " | Ramlatech"
            write(ROOT / url.lstrip("/"), subpage(filled, url=url, title=title, index=page == 1))

    for p in published:
        write(OUT_DIR / f"{p.slug}.html", render_post(p, published, nav, footer))
    write(OUT_DIR / "index.html", f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><title>Ramlatech Blog</title>
<link rel="canonical" href="{SITE}/blog.html" /><meta name="robots" content="noindex, follow" />
<meta http-equiv="refresh" content="0; url=/blog.html" /></head><body><a href="/blog.html">Ramlatech Blog</a></body></html>
""")
    write(OUT_DIR / "feed.xml", render_feed(published))
    update_sitemap(published)
    scheduled = [p for p in posts if not p.draft and p.date > now]
    drafts = [p for p in posts if p.draft]
    print(f"Built blog: {len(published)} published, {len(scheduled)} scheduled, {len(drafts)} drafts.")
    return published


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--now", help="pretend the current time is this ISO datetime (testing)")
    args = ap.parse_args()
    now = parse_date(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    build(now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
