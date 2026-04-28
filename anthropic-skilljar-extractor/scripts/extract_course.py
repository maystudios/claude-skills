#!/usr/bin/env python3
"""
Anthropic Skilljar Course Extractor
Usage: python extract_course.py <skilljar_url> [output_dir]

Extracts course structure, lesson notes, and images from an Anthropic Academy
Skilljar course page into a structured markdown folder.
"""

import sys, os, re, json, urllib.request, urllib.error

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8", errors="replace")

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def extract_chat_data(html):
    idx = html.find("window.__chatData = ")
    if idx == -1:
        return {}
    obj_start = html.find("{", idx)
    depth, i = 0, obj_start
    while i < len(html):
        if html[i] == "{": depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0: break
        i += 1
    try:
        return json.loads(html[obj_start:i+1])
    except Exception:
        return {}

def extract_curriculum(html):
    """Returns list of {'section': str, 'title': str, 'url': str, 'id': str}"""
    # Find the HTML <ul> element (skip CSS occurrences)
    curr_start = -1
    pos = 0
    while True:
        pos = html.find("dp-curriculum", pos)
        if pos == -1:
            break
        # Must be inside a <ul> tag, not CSS
        if "<ul" in html[max(0, pos-10):pos+20]:
            curr_start = pos
            break
        pos += 1
    if curr_start == -1:
        # Fallback: find by lesson-video class in list items
        curr_start = html.find('class=" lesson-video"')
        if curr_start == -1:
            curr_start = html.find('lesson-video" data-url=')
        if curr_start == -1:
            return []
        curr_start = max(0, curr_start - 5000)
    block = html[curr_start:curr_start + 40000]
    items = re.findall(
        r'<li class="section[^"]*">(.*?)</li>'
        r'|<li class="[^"]*lesson[^"]*" data-url="([^"]+)">(.*?)</li>',
        block, re.DOTALL
    )
    results, current_section, seen_urls = [], "Introduction", set()
    for sec_raw, url, lesson_raw in items:
        if sec_raw.strip():
            current_section = re.sub(r"<[^>]+>", "", sec_raw).strip()
        elif url and url not in seen_urls:
            seen_urls.add(url)
            title_m = re.search(r"<div>(.*?)<span", lesson_raw, re.DOTALL)
            title = re.sub(r"<[^>]+>", "", title_m.group(1) if title_m else lesson_raw).strip()
            lesson_id = url.rstrip("/").split("/")[-1]
            results.append({"section": current_section, "title": title, "url": url, "id": lesson_id})
    return results

def extract_notes(chat_data, course_slug):
    """Find the right key in chatData for this course."""
    # Try known key patterns
    candidates = [
        course_slug.replace("-", "_"),
        "mcp_intro", "mcp_advanced", "claudecode", "1p", "bedrock", "vertex"
    ]
    # Also try by checking which key has notes matching course slug keywords
    slug_words = set(course_slug.replace("-", " ").split())
    for key, val in chat_data.items():
        if isinstance(val, str) and len(val) > 500:
            notes = re.findall(r'<note title="([^"]+)">(.*?)</note>', val, re.DOTALL)
            if notes:
                candidates.insert(0, key)
                break
    for key in candidates:
        if key in chat_data:
            val = chat_data[key]
            if isinstance(val, str):
                notes = re.findall(r'<note title="([^"]+)">(.*?)</note>', val, re.DOTALL)
                if notes:
                    return {t.strip(): b.strip() for t, b in notes}
    return {}

def extract_section_images(html, course_slug):
    """Find CloudFront image URLs for this course."""
    pattern = rf'https://d7juhi4i8fsw0\.cloudfront\.net/images/{re.escape(course_slug)}/([^"\']+\.webp)'
    urls = list(dict.fromkeys(re.findall(pattern, html)))
    return [f"https://d7juhi4i8fsw0.cloudfront.net/images/{course_slug}/{u}" for u in urls]

def download_image(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            with open(dest_path, "wb") as f:
                f.write(r.read())
        return True
    except Exception:
        return False

def note_key_match(note_title, lesson_title):
    """Fuzzy match note title to lesson title."""
    def norm(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())
    nt, lt = norm(note_title), norm(lesson_title)
    return nt == lt or nt in lt or lt in nt

def make_lesson_md(lesson, notes, images_dir, course_url, section_images):
    title = lesson["title"]
    section = lesson["section"]
    url = f"https://anthropic.skilljar.com{lesson['url']}"

    # Find matching note
    note_body = ""
    for note_title, body in notes.items():
        if note_key_match(note_title, title):
            note_body = body
            break

    lines = [
        f"# {title}",
        "",
        f"**Section:** {section}",
        f"**Course:** Introduction to Model Context Protocol",
        f"**Lesson Type:** Video Lesson",
        f"**URL:** {url}",
        "",
        "---",
        "",
    ]

    if note_body:
        lines.append("## Lesson Notes")
        lines.append("")
        # Convert bullet-point notes to readable markdown
        for line in note_body.splitlines():
            line = line.rstrip()
            if not line:
                lines.append("")
            elif re.match(r"^[A-Z][^:]+:\s", line) and len(line) < 120:
                # "Key Term: description" -> bold key
                parts = line.split(": ", 1)
                lines.append(f"**{parts[0]}:** {parts[1] if len(parts) > 1 else ''}")
            else:
                lines.append(line)
        lines.append("")
    else:
        lines.append(f"*No lesson notes extracted — this lesson may be a survey, assessment, or welcome video.*")
        lines.append("")

    return "\n".join(lines)

def make_readme(course_title, course_url, sections_map, image_files):
    lines = [
        f"# {course_title}",
        "",
        f"**Source:** {course_url}",
        f"**Provider:** Anthropic Academy",
        "",
        "---",
        "",
        "## Course Structure",
        "",
    ]
    for section, lessons in sections_map.items():
        folder = f"{list(sections_map.keys()).index(section)+1:02d}-{slugify(section)}"
        lines.append(f"### {section}")
        for i, lesson in enumerate(lessons, 1):
            fname = f"{i:02d}-{slugify(lesson['title'])}.md"
            lines.append(f"- [{lesson['title']}]({folder}/{fname})")
        lines.append("")

    if image_files:
        lines += ["## Course Diagrams", "", "Saved in `assets/images/`:", ""]
        for img in image_files:
            lines.append(f"- `{os.path.basename(img)}`")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_course.py <skilljar_url> [output_dir]")
        sys.exit(1)

    url = sys.argv[1].rstrip("/")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    # Derive course slug from URL
    course_slug = url.split("/")[-1]
    print(f"Fetching: {url}")
    html = fetch(url)
    print(f"  Page size: {len(html)} bytes")

    # Extract data
    chat_data = extract_chat_data(html)
    curriculum = extract_curriculum(html)
    notes = extract_notes(chat_data, course_slug)
    image_urls = extract_section_images(html, course_slug)

    print(f"  Sections/lessons: {len(curriculum)}")
    print(f"  Lesson notes found: {len(notes)}")
    print(f"  Section images: {len(image_urls)}")

    if not curriculum:
        print("ERROR: Could not extract curriculum. The page may require login.")
        sys.exit(1)

    # Derive course title
    title_m = re.search(r"<title>(.*?)</title>", html)
    course_title = title_m.group(1).strip() if title_m else course_slug.replace("-", " ").title()

    # Build section map
    sections_map = {}
    for lesson in curriculum:
        sections_map.setdefault(lesson["section"], []).append(lesson)

    # Create output directories
    base = os.path.join(output_dir, course_slug)
    os.makedirs(base, exist_ok=True)
    images_dir = os.path.join(base, "assets", "images")
    os.makedirs(images_dir, exist_ok=True)

    # Download images
    downloaded_images = []
    for img_url in image_urls:
        fname = img_url.split("/")[-1]
        dest = os.path.join(images_dir, fname)
        if download_image(img_url, dest):
            downloaded_images.append(dest)
            print(f"  Downloaded image: {fname}")

    # Write lesson markdown files
    for section_idx, (section, lessons) in enumerate(sections_map.items(), 1):
        folder_name = f"{section_idx:02d}-{slugify(section)}"
        folder = os.path.join(base, folder_name)
        os.makedirs(folder, exist_ok=True)

        for lesson_idx, lesson in enumerate(lessons, 1):
            fname = f"{lesson_idx:02d}-{slugify(lesson['title'])}.md"
            content = make_lesson_md(lesson, notes, images_dir, url, image_urls)
            with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Wrote: {folder_name}/{fname}")

    # Write README
    readme = make_readme(course_title, url, sections_map, downloaded_images)
    with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"  Wrote: README.md")

    print(f"\nDone! Output in: {base}")
    print(f"  {len(curriculum)} lessons across {len(sections_map)} sections")
    print(f"  {len(downloaded_images)} images downloaded")
    print(f"  {len(notes)} lesson notes embedded")
    print()
    print("Next step: Open each markdown file and enrich with image alt-text descriptions")
    print("using the Read tool on the downloaded .webp files in assets/images/")

if __name__ == "__main__":
    main()
