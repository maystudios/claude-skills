#!/usr/bin/env python3
"""
Download videos from URLs and generate a Markdown summary for each one.

Each video gets its own subfolder:
  <output_dir>/<sanitized_title>/
      <video_file>.mp4
      summary.md

Usage:
    py fetch_and_summarize.py <url1> [url2 ...] [-o output_dir]
    py fetch_and_summarize.py --file links.txt [-o output_dir]
    py fetch_and_summarize.py --file links.md  [-o output_dir]

Requires:
    GEMINI_API_KEY environment variable
    pip install yt-dlp google-genai
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-3-flash-preview"

SUMMARY_PROMPT = """Analyze this video thoroughly and produce a structured Markdown summary.
Match the language of the summary to the language spoken/shown in the video.

Use exactly this structure (keep the headings as-is):

# [Title]

## Summary
[2-3 sentence paragraph describing what the video is about and its main topic]

## Key Points
- [key point 1]
- [key point 2]
- [key point 3]
- [add more as needed]

## Core Content & Takeaways
[What is the central message or most important insight from this video? 2-4 sentences that capture the essence.]

---
*Auto-generated with Gemini API*
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_package(package: str):
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package, "-q"], check=True)


def sanitize_name(name: str, max_len: int = 80) -> str:
    """Turn an arbitrary string into a safe folder name."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = name.strip("._")
    return name[:max_len] or "video"


def extract_urls_from_text(text: str) -> list[str]:
    """Extract all http/https URLs from a block of text."""
    return re.findall(r'https?://[^\s\)\]\'"<>]+', text)


def load_urls(sources: list[str]) -> list[str]:
    """
    sources can be a mix of:
      - raw URLs (http/https)
      - file paths (.txt, .md, or any text file)
    Returns a deduplicated list of URLs.
    """
    urls = []
    for src in sources:
        if src.startswith("http://") or src.startswith("https://"):
            urls.append(src)
        else:
            p = pathlib.Path(src)
            if not p.exists():
                print(f"WARNING: file not found: {src}", file=sys.stderr)
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            found = extract_urls_from_text(text)
            print(f"Found {len(found)} URL(s) in {p.name}")
            urls.extend(found)

    # deduplicate while preserving order
    seen = set()
    result = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def get_video_info(url: str) -> dict:
    """Fetch video metadata (title, id, uploader) via yt-dlp --dump-json."""
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--dump-json", "--no-playlist", url],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout.strip().splitlines()[0])
    except json.JSONDecodeError:
        return {}


def download_video(url: str, output_dir: pathlib.Path, cookies_from_browser: str = None) -> pathlib.Path | None:
    """
    Download a single video into output_dir.
    Returns the path to the downloaded .mp4, or None on failure.
    """
    output_template = str(output_dir / "%(uploader)s_%(id)s.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--output", output_template,
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--progress",
    ]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    cmd.append(url)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        return None

    mp4_files = sorted(output_dir.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    return mp4_files[0] if mp4_files else None


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------

def wait_for_file_active(client, file_obj, timeout=300):
    start = time.time()
    while True:
        f = client.files.get(name=file_obj.name)
        state = f.state.name if hasattr(f.state, "name") else str(f.state)
        if state == "ACTIVE":
            return f
        if state == "FAILED":
            raise RuntimeError(f"File processing failed: {file_obj.name}")
        if time.time() - start > timeout:
            raise TimeoutError(f"File not ACTIVE after {timeout}s")
        time.sleep(4)


def summarize_video(client, video_path: pathlib.Path, prompt: str = SUMMARY_PROMPT) -> str:
    print(f"  Uploading to Gemini ...", flush=True)
    uploaded = client.files.upload(
        file=str(video_path),
        config={"mime_type": "video/mp4", "display_name": video_path.stem},
    )
    print(f"  Waiting for processing ...", flush=True)
    uploaded = wait_for_file_active(client, uploaded)

    print(f"  Generating summary ...", flush=True)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[uploaded, prompt],
    )
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass
    return response.text


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_url(url: str, base_output_dir: pathlib.Path, gemini_client, cookies_from_browser: str = None, prompt: str = SUMMARY_PROMPT):
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    # 1. Get metadata to build a nice folder name
    print("  Fetching metadata ...")
    info = get_video_info(url)
    title = info.get("title") or info.get("id") or "video"
    folder_name = sanitize_name(title)
    video_dir = base_output_dir / folder_name
    video_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Folder: {video_dir}")

    # Skip if summary already exists
    summary_path = video_dir / "summary.md"
    existing_mp4 = list(video_dir.glob("*.mp4"))
    if summary_path.exists() and existing_mp4:
        print("  SKIP: already downloaded and summarized.")
        return True

    # 2. Download
    print(f"  Downloading video ...")
    mp4_path = download_video(url, video_dir, cookies_from_browser)
    if not mp4_path:
        print(f"  ERROR: Download failed.", file=sys.stderr)
        return False
    print(f"  Downloaded: {mp4_path.name}")

    # 3. Summarize
    try:
        summary_text = summarize_video(gemini_client, mp4_path, prompt)
        summary_path.write_text(summary_text, encoding="utf-8")
        print(f"  Summary saved: {summary_path}")
        return True
    except Exception as e:
        print(f"  ERROR during summarization: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download videos and generate Markdown summaries, one folder per video."
    )
    parser.add_argument(
        "sources", nargs="*",
        help="Video URLs and/or paths to files containing URLs (.txt, .md, etc.)"
    )
    parser.add_argument(
        "--file", "-f", dest="files", action="append", default=[],
        help="Text/Markdown file containing video URLs (can be used multiple times)"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Base output directory (default: current working directory)"
    )
    parser.add_argument(
        "--cookies-from-browser", default=None,
        help="Browser to pull cookies from (chrome/firefox/edge/safari)"
    )
    parser.add_argument(
        "--prompt", "-p", default=None,
        help="Custom prompt to use instead of the default summary prompt"
    )
    parser.add_argument(
        "--prompt-file", default=None,
        help="Path to a text file containing a custom prompt"
    )
    args = parser.parse_args()

    # Collect all sources
    all_sources = list(args.sources) + list(args.files)
    if not all_sources:
        parser.print_help()
        sys.exit(1)

    # Resolve URLs
    urls = load_urls(all_sources)
    if not urls:
        print("ERROR: No URLs found in the provided sources.", file=sys.stderr)
        sys.exit(1)

    # Resolve custom prompt
    prompt = SUMMARY_PROMPT
    if args.prompt:
        prompt = args.prompt
        print(f"Using custom inline prompt.")
    elif args.prompt_file:
        pf = pathlib.Path(args.prompt_file)
        if not pf.exists():
            print(f"ERROR: Prompt file not found: {pf}", file=sys.stderr)
            sys.exit(1)
        prompt = pf.read_text(encoding="utf-8").strip()
        if not prompt:
            print(f"ERROR: Prompt file is empty: {pf}", file=sys.stderr)
            sys.exit(1)
        print(f"Using custom prompt from: {pf}")

    print(f"\nProcessing {len(urls)} video(s)...")

    # Check prerequisites
    ensure_package("yt-dlp")
    ensure_package("google-genai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    gemini_client = genai.Client(api_key=api_key)

    base_output_dir = pathlib.Path(args.output) if args.output else pathlib.Path.cwd()
    base_output_dir.mkdir(parents=True, exist_ok=True)

    success, failed = 0, 0
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", end="")
        ok = process_url(url, base_output_dir, gemini_client, args.cookies_from_browser, prompt)
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n\n{'='*60}")
    print(f"Done: {success} succeeded, {failed} failed")
    print(f"Output: {base_output_dir}")


if __name__ == "__main__":
    main()
