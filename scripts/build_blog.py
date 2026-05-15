#!/usr/bin/env python3
"""Build Markdown posts into static blog pages and archive data.

Dependencies:
    pip install python-frontmatter markdown
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

try:
    import frontmatter  # type: ignore
except ImportError:  # pragma: no cover - depends on local environment
    frontmatter = None

try:
    import markdown  # type: ignore
except ImportError:  # pragma: no cover - depends on local environment
    markdown = None


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "blog"
BLOG_DIR = ROOT / "blog"
TEMPLATE_PATH = ROOT / "templates" / "blog-post-template.html"
DATA_DIR = ROOT / "data"
BLOG_INDEX_PATH = BLOG_DIR / "index.html"
POSTS_JSON_PATH = DATA_DIR / "blog-posts.json"
MANIFEST_PATH = DATA_DIR / "generated-blog-pages.json"

REQUIRED_FIELDS = ("title", "slug", "date", "description", "category")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class MarkdownDocument:
    metadata: dict[str, Any]
    content: str


def parse_simple_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value == "[]":
        return []
    return value


def load_markdown_document(source_path: Path) -> MarkdownDocument:
    if frontmatter is not None:
        loaded = frontmatter.load(source_path)
        return MarkdownDocument(metadata=dict(loaded.metadata), content=loaded.content)

    text = source_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail(f"{source_path}: missing YAML frontmatter block.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        fail(f"{source_path}: missing closing YAML frontmatter delimiter.")

    metadata: dict[str, Any] = {}
    current_list_key = ""
    for raw_line in parts[1].splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        if current_list_key and line.startswith(("  - ", "    - ")):
            metadata[current_list_key].append(parse_simple_value(line.split("- ", 1)[1]))
            continue
        current_list_key = ""
        if ":" not in line:
            fail(f"{source_path}: unsupported frontmatter line: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = parse_simple_value(raw_value)
        metadata[key] = value
        if value == "" and key == "tags":
            metadata[key] = []
            current_list_key = key

    return MarkdownDocument(metadata=metadata, content=parts[2].lstrip("\n"))


def render_inline_markdown(text: str) -> str:
    rendered = escape(text)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", rendered)
    rendered = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{escape(m.group(2), quote=True)}">{m.group(1)}</a>', rendered)
    return rendered


def flush_paragraph(lines: list[str], html_lines: list[str]) -> None:
    if lines:
        html_lines.append(f"<p>{render_inline_markdown(' '.join(line.strip() for line in lines))}</p>")
        lines.clear()


def flush_list(list_items: list[str], html_lines: list[str], ordered: bool) -> None:
    if list_items:
        tag = "ol" if ordered else "ul"
        html_lines.append(f"<{tag}>")
        for item in list_items:
            html_lines.append(f"<li>{render_inline_markdown(item)}</li>")
        html_lines.append(f"</{tag}>")
        list_items.clear()


def convert_markdown(content: str) -> str:
    if markdown is not None:
        return markdown.markdown(
            content,
            extensions=["extra", "sane_lists", "toc"],
            output_format="html5",
        )

    html_lines: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_ordered = False
    in_code = False
    code_lines: list[str] = []
    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph(paragraph, html_lines)
                flush_list(list_items, html_lines, list_ordered)
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not stripped:
            flush_paragraph(paragraph, html_lines)
            flush_list(list_items, html_lines, list_ordered)
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph(paragraph, html_lines)
            flush_list(list_items, html_lines, list_ordered)
            level = len(heading_match.group(1))
            heading_text = render_inline_markdown(heading_match.group(2))
            html_lines.append(f"<h{level}>{heading_text}</h{level}>")
            continue
        quote_match = re.match(r"^>\s?(.*)$", stripped)
        if quote_match:
            flush_paragraph(paragraph, html_lines)
            flush_list(list_items, html_lines, list_ordered)
            html_lines.append(f"<blockquote><p>{render_inline_markdown(quote_match.group(1))}</p></blockquote>")
            continue
        unordered_match = re.match(r"^[-*+]\s+(.+)$", stripped)
        ordered_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if unordered_match or ordered_match:
            flush_paragraph(paragraph, html_lines)
            ordered = ordered_match is not None
            if list_items and ordered != list_ordered:
                flush_list(list_items, html_lines, list_ordered)
            list_ordered = ordered
            list_items.append((ordered_match or unordered_match).group(1))
            continue
        paragraph.append(stripped)

    flush_paragraph(paragraph, html_lines)
    flush_list(list_items, html_lines, list_ordered)
    if in_code:
        html_lines.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(html_lines)


@dataclass
class BlogPost:
    source_path: Path
    title: str
    slug: str
    date: str
    display_date: str
    updated: str
    display_updated: str
    description: str
    author: str
    category: str
    tags: list[str]
    cover_image: str
    cover_alt: str
    canonical_url: str
    url: str
    content_html: str

    def json_record(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "date": self.date,
            "displayDate": self.display_date,
            "updated": self.updated,
            "displayUpdated": self.display_updated,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "coverImage": self.cover_image,
            "coverAlt": self.cover_alt,
            "canonicalUrl": self.canonical_url,
            "url": self.url,
        }


def fail(message: str) -> None:
    raise SystemExit(f"Error: {message}")


def parse_date(value: Any, field_name: str, source_path: Path) -> tuple[str, str]:
    if value in (None, ""):
        return "", ""

    if isinstance(value, datetime):
        date_value = value.date()
    else:
        text_value = str(value).strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text_value):
            fail(f"{source_path}: field '{field_name}' must use YYYY-MM-DD format.")
        try:
            date_value = datetime.strptime(text_value, "%Y-%m-%d").date()
        except ValueError:
            fail(f"{source_path}: field '{field_name}' is not a valid date: {text_value}")

    iso_value = date_value.isoformat()
    return iso_value, f"{date_value.strftime('%B')} {date_value.day}, {date_value.year}"


def scalar_metadata(metadata: dict[str, Any], field_name: str, source_path: Path, default: str = "") -> str:
    value = metadata.get(field_name, default)
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        fail(f"{source_path}: field '{field_name}' must be a scalar value.")
    return str(value).strip()


def tags_metadata(metadata: dict[str, Any], source_path: Path) -> list[str]:
    value = metadata.get("tags", [])
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        fail(f"{source_path}: field 'tags' must be a YAML list when provided.")
    return [str(tag).strip() for tag in value if str(tag).strip()]


def load_markdown_posts() -> list[BlogPost]:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    markdown_files = sorted(CONTENT_DIR.glob("*.md"))
    posts: list[BlogPost] = []
    seen_slugs: dict[str, Path] = {}

    for source_path in markdown_files:
        post = load_markdown_document(source_path)
        metadata = post.metadata

        for field in REQUIRED_FIELDS:
            if scalar_metadata(metadata, field, source_path) == "":
                fail(f"{source_path}: missing required field '{field}'.")

        title = scalar_metadata(metadata, "title", source_path)
        slug = scalar_metadata(metadata, "slug", source_path)
        if not SLUG_RE.fullmatch(slug):
            fail(
                f"{source_path}: field 'slug' must contain lowercase letters, "
                "numbers, and single hyphens only."
            )
        if slug in seen_slugs:
            fail(f"duplicate slug '{slug}' in {seen_slugs[slug]} and {source_path}.")
        seen_slugs[slug] = source_path

        date, display_date = parse_date(metadata.get("date"), "date", source_path)
        updated, display_updated = parse_date(metadata.get("updated"), "updated", source_path)
        description = scalar_metadata(metadata, "description", source_path)
        author = scalar_metadata(metadata, "author", source_path, "B. H. Schafer") or "B. H. Schafer"
        category = scalar_metadata(metadata, "category", source_path)
        tags = tags_metadata(metadata, source_path)
        cover_image = scalar_metadata(metadata, "cover_image", source_path)
        cover_alt = scalar_metadata(metadata, "cover_alt", source_path)
        canonical_url = scalar_metadata(metadata, "canonical_url", source_path)

        content_html = convert_markdown(post.content)

        posts.append(
            BlogPost(
                source_path=source_path,
                title=title,
                slug=slug,
                date=date,
                display_date=display_date,
                updated=updated,
                display_updated=display_updated,
                description=description,
                author=author,
                category=category,
                tags=tags,
                cover_image=cover_image,
                cover_alt=cover_alt,
                canonical_url=canonical_url,
                url=f"/blog/{slug}/",
                content_html=content_html,
            )
        )

    return sorted(posts, key=lambda item: item.date, reverse=True)


def safe_blog_dir_for_slug(slug: str) -> Path:
    target = (BLOG_DIR / slug).resolve()
    blog_root = BLOG_DIR.resolve()
    if target == blog_root or blog_root not in target.parents:
        fail(f"refusing unsafe blog output path for slug '{slug}'.")
    return target


def read_previous_manifest() -> list[str]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail(f"{MANIFEST_PATH}: generated page manifest is not valid JSON.")

    if isinstance(manifest, dict):
        slugs = manifest.get("slugs", [])
    else:
        slugs = manifest

    if not isinstance(slugs, list):
        fail(f"{MANIFEST_PATH}: expected a list of generated slugs.")
    return [str(slug) for slug in slugs]


def delete_previous_generated_pages() -> list[str]:
    deleted: list[str] = []
    for slug in read_previous_manifest():
        if not SLUG_RE.fullmatch(slug):
            print(f"Skipping unsafe generated slug in manifest: {slug}")
            continue
        target = safe_blog_dir_for_slug(slug)
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            deleted.append(slug)
    return deleted


def render_template(template: str, post: BlogPost) -> str:
    canonical_link = ""
    if post.canonical_url:
        canonical_link = f'<link rel="canonical" href="{escape(post.canonical_url, quote=True)}">'

    updated_markup = ""
    if post.display_updated:
        updated_markup = f'<p class="blog-updated">Updated {escape(post.display_updated)}</p>'

    cover_markup = ""
    if post.cover_image:
        alt_text = escape(post.cover_alt or post.title, quote=True)
        cover_markup = (
            '<figure class="blog-cover">\n'
            f'\t\t\t\t\t\t\t\t<img src="{escape(post.cover_image, quote=True)}" alt="{alt_text}" />\n'
            "\t\t\t\t\t\t\t</figure>"
        )

    replacements = {
        "{{ title }}": escape(post.title),
        "{{ description }}": escape(post.description, quote=True),
        "{{ display_date }}": escape(post.display_date),
        "{{ display_updated }}": updated_markup,
        "{{ content }}": post.content_html,
        "{{ author }}": escape(post.author),
        "{{ category }}": escape(post.category),
        "{{ canonical_url }}": canonical_link,
        "{{ cover_image }}": cover_markup,
        "{{ cover_alt }}": escape(post.cover_alt, quote=True),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"


def write_blog_pages(posts: list[BlogPost]) -> None:
    if not TEMPLATE_PATH.exists():
        fail(f"template file is missing: {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for post in posts:
        output_dir = safe_blog_dir_for_slug(post.slug)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(render_template(template, post), encoding="utf-8")


def render_archive_card(post: BlogPost) -> str:
    title = escape(post.title)
    description = escape(post.description)
    category = escape(post.category)
    display_date = escape(post.display_date)
    url = escape(post.url, quote=True)
    return f'''\t\t\t\t\t\t\t\t<article class="blog-preview">
\t\t\t\t\t\t\t\t\t<div class="blog-preview-content">
\t\t\t\t\t\t\t\t\t\t<h3><a href="{url}">{title}</a></h3>
\t\t\t\t\t\t\t\t\t\t<p class="blog-date">{display_date}</p>
\t\t\t\t\t\t\t\t\t\t<p class="blog-description">{description}</p>
\t\t\t\t\t\t\t\t\t\t<p class="blog-category">{category}</p>
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="blog-preview-action">
\t\t\t\t\t\t\t\t\t\t<a href="{url}" class="button">Read &rarr;</a>
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t</article>'''


def update_archive_fallback(posts: list[BlogPost]) -> bool:
    if not BLOG_INDEX_PATH.exists():
        print(f"Skipping archive fallback update; missing {BLOG_INDEX_PATH}")
        return False

    archive = BLOG_INDEX_PATH.read_text(encoding="utf-8")
    start_marker = "<!-- BLOG_POSTS_START -->"
    end_marker = "<!-- BLOG_POSTS_END -->"
    start = archive.find(start_marker)
    end = archive.find(end_marker)
    if start == -1 or end == -1 or end < start:
        print("Skipping archive fallback update; BLOG_POSTS markers not found.")
        return False

    cards = "\n" + "\n".join(render_archive_card(post) for post in posts) + "\n\t\t\t\t\t\t\t"
    updated = archive[: start + len(start_marker)] + cards + archive[end:]
    BLOG_INDEX_PATH.write_text(updated, encoding="utf-8")
    return True


def write_data_files(posts: list[BlogPost]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_JSON_PATH.write_text(
        json.dumps([post.json_record() for post in posts], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MANIFEST_PATH.write_text(
        json.dumps([post.slug for post in posts], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    posts = load_markdown_posts()
    deleted = delete_previous_generated_pages()
    write_blog_pages(posts)
    write_data_files(posts)
    archive_updated = update_archive_fallback(posts)

    print("Blog build complete.")
    print(f"  Source posts: {len(posts)}")
    print(f"  Generated pages: {len(posts)}")
    print(f"  Deleted previously generated folders: {len(deleted)}")
    if deleted:
        print("    " + ", ".join(deleted))
    print(f"  Wrote: {POSTS_JSON_PATH.relative_to(ROOT)}")
    print(f"  Wrote: {MANIFEST_PATH.relative_to(ROOT)}")
    if archive_updated:
        print(f"  Updated archive fallback: {BLOG_INDEX_PATH.relative_to(ROOT)}")
    if not posts:
        print(f"  No Markdown files found in {CONTENT_DIR.relative_to(ROOT)}; generated empty data files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
