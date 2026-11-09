#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a static course website for 《AI 全栈编程生存指南》 from markdown chapters."""
import os
import re
import html
import shutil
import unicodedata
from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "site")
BOOK_TITLE = "AI 全栈编程生存指南"
BOOK_SUBTITLE = "从 0 到 1，构建一个能活下去的全栈产品"
REPO = "https://github.com/toly1994328/flash_im_by_ai"

BOX_CHARS = set("─│┌┐└┘├┤┬┴┼▶◀▼▲╭╮╯╰═║╔╗╚╝━┃┏┓┗┛┣┫┳┻╋")
DIAGRAM_INNER = 736
DIAGRAM_MIN_FONT = 9.0
DIAGRAM_MAX_FONT = 13.5
TOC_LEVELS = ("h2", "h3", "h4", "h5")


def cell_width(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def diagram_font_size(content):
    cells = max((cell_width(line) for line in content.splitlines()), default=0)
    if cells == 0:
        return None
    size = DIAGRAM_INNER / (cells * 0.6)
    return round(max(DIAGRAM_MIN_FONT, min(DIAGRAM_MAX_FONT, size)), 1)


def is_diagram(content):
    if not any(c in BOX_CHARS for c in content):
        return False
    cells = max((cell_width(line) for line in content.splitlines()), default=0)
    return cells <= 170


def strip_frontmatter(text):
    if text.lstrip().startswith("---"):
        m = re.match(r"^\s*---\s*\n.*?\n---\s*\n", text, re.S)
        if m:
            return text[m.end():]
    return text


def read_chapters():
    chapters = []
    for name in os.listdir(SRC):
        if not name.endswith(".md"):
            continue
        m = re.match(r"^(\d+)-(.+)\.md$", name)
        if not m:
            continue
        num = int(m.group(1))
        title = m.group(2).strip()
        with open(os.path.join(SRC, name), encoding="utf-8") as f:
            text = strip_frontmatter(f.read())
        chapters.append({"num": num, "title": title, "text": text})
    chapters.sort(key=lambda c: c["num"])
    return chapters


def reading_time(text):
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    minutes = cjk / 450.0 + words / 220.0
    total = max(30, int(round(minutes * 60)))
    mm, ss = divmod(total, 60)
    return f"{mm}分{ss}秒" if mm else f"{ss}秒"


def build_renderer():
    md = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    return md


def clean_inline(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"\*(?!\s)", "", text)
    return text.strip()


def process_tokens(tokens):
    toc = []
    used = {}
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in TOC_LEVELS:
            inline = tokens[i + 1]
            title = clean_inline(inline.content)
            base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-").lower() or "sec"
            idx = used.get(base, 0)
            used[base] = idx + 1
            hid = base if idx == 0 else f"{base}-{idx}"
            tok.attrSet("id", hid)
            toc.append({"id": hid, "text": title, "level": int(tok.tag[1])})
        elif tok.type == "fence" and is_diagram(tok.content):
            size = diagram_font_size(tok.content)
            tok.attrSet("class", "diagram")
            if size is not None:
                tok.attrSet("style", f"font-size:{size}px")
    return toc


def render_chapter(md, c):
    text = f"# {c['title']}\n\n" + c["text"].lstrip("\n")
    tokens = md.parse(text)
    toc = process_tokens(tokens)
    body = md.renderer.render(tokens, md.options, {})
    return body, toc


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>{page_title} - {book_title}</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css">
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <a class="topbar-title" href="index.html">{book_title}</a>
    <div class="topbar-right">
      <a class="login-btn" href="{repo}" target="_blank" rel="noopener">项目源码</a>
    </div>
  </div>
</header>

<div class="layout">
  <aside class="sidebar">
    <nav class="chapter-list">
      <ol>
        {chapter_items}
      </ol>
    </nav>
  </aside>

  <main class="content">
    <article class="markdown-body">
      {body}
    </article>
    <div class="pager">
      {prev_link}
      {next_link}
    </div>
  </main>

  <aside class="toc">
    <div class="toc-head"><span>目录</span><span class="toc-toggle">≫</span></div>
    <ul>{toc_items}</ul>
  </aside>
</div>

<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/common.min.js"></script>
<script>hljs.highlightAll();</script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def make_chapter_items(chapters, active_id):
    items = []
    for c in chapters:
        cls = ' class="active"' if c["id"] == active_id else ""
        items.append(
            f'<li{cls}><a href="{c["id"]}.html">'
            f'<span class="num">{c["num"]}</span>'
            f'<span class="info"><span class="t">{html.escape(c["title"])}</span>'
            f'<span class="d">阅读时长: {c["time"]}</span></span>'
            f'</a></li>'
        )
    return "\n        ".join(items)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for asset in ("style.css", "app.js"):
        shutil.copy(os.path.join(ROOT, "web", asset), os.path.join(OUT, "assets", asset))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    md = build_renderer()
    chapters = read_chapters()
    for c in chapters:
        c["id"] = f"ch-{c['num']}"
        c["time"] = reading_time(c["text"])
        c["html"], c["toc"] = render_chapter(md, c)

    for i, c in enumerate(chapters):
        toc_items = "\n      ".join(
            f'<li class="lv{min(t["level"], 5)}"><a href="#{t["id"]}">{html.escape(t["text"])}</a></li>'
            for t in c["toc"]
        ) or '<li class="muted">（本章无小节）</li>'
        prev_link = next_link = ""
        if i > 0:
            p = chapters[i - 1]
            prev_link = f'<a class="prev" href="{p["id"]}.html">← {html.escape(p["title"])}</a>'
        if i < len(chapters) - 1:
            n = chapters[i + 1]
            next_link = f'<a class="next" href="{n["id"]}.html">{html.escape(n["title"])} →</a>'
        page = PAGE.format(
            page_title=html.escape(c["title"]),
            book_title=html.escape(BOOK_TITLE),
            repo=REPO,
            chapter_items=make_chapter_items(chapters, c["id"]),
            body=c["html"],
            toc_items=toc_items,
            prev_link=prev_link,
            next_link=next_link,
        )
        with open(os.path.join(OUT, f'{c["id"]}.html'), "w", encoding="utf-8") as f:
            f.write(page)

    first = chapters[0]
    cards = "\n      ".join(
        f'<a class="card" href="{c["id"]}.html"><span class="card-num">{c["num"]:02d}</span>'
        f'<span class="card-t">{html.escape(c["title"])}</span>'
        f'<span class="card-d">{c["time"]}</span></a>'
        for c in chapters
    )
    index = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="referrer" content="no-referrer">
<title>{html.escape(BOOK_TITLE)}</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="landing-body">
<header class="topbar">
  <div class="topbar-inner">
    <a class="topbar-title" href="index.html">{html.escape(BOOK_TITLE)}</a>
    <div class="topbar-right">
      <a class="login-btn" href="{REPO}" target="_blank" rel="noopener">项目源码</a>
    </div>
  </div>
</header>
<div class="landing">
  <h1>{html.escape(BOOK_TITLE)}</h1>
  <p class="sub">{html.escape(BOOK_SUBTITLE)}</p>
  <p class="desc">共 {len(chapters)} 篇 · 用一个真实的全栈即时通讯项目，串起 AI 时代的完整开发流程。</p>
  <a class="start-btn" href="{first['id']}.html">开始阅读</a>
  <div class="cards">
      {cards}
  </div>
</div>
</body>
</html>
"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)

    print(f"Generated {len(chapters)} chapters into {OUT}")


if __name__ == "__main__":
    main()
