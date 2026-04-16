#!/usr/bin/env python3
"""
Summarizes MP4 videos using the Gemini API.
Uploads each video via the Files API, generates a structured Markdown
summary, and saves it as a .md file next to the original video.

Usage:
    py summarize_videos.py [directory]                        # default prompt
    py summarize_videos.py [directory] --prompt "Extract ..."  # custom prompt (inline)
    py summarize_videos.py [directory] --prompt-file p.txt     # custom prompt (from file)

Requires:
    GEMINI_API_KEY environment variable
    pip install google-genai
"""

import argparse
import os
import sys
import time
import pathlib

MODEL = "gemini-3-flash-preview"

PROMPT = """Analyze this video thoroughly and produce a structured Markdown summary.
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


def wait_for_file_active(client, file_obj, timeout=300):
    """Poll until the uploaded file reaches ACTIVE state."""
    start = time.time()
    while True:
        f = client.files.get(name=file_obj.name)
        state = f.state.name if hasattr(f.state, "name") else str(f.state)
        if state == "ACTIVE":
            return f
        if state == "FAILED":
            raise RuntimeError(f"File processing failed for: {file_obj.name}")
        if time.time() - start > timeout:
            raise TimeoutError(f"File not ACTIVE after {timeout}s: {file_obj.name}")
        time.sleep(4)


def summarize_video(client, video_path: pathlib.Path, prompt: str = PROMPT) -> str:
    print(f"  Uploading {video_path.name} ...", flush=True)
    uploaded = client.files.upload(
        file=str(video_path),
        config={"mime_type": "video/mp4", "display_name": video_path.stem},
    )

    print(f"  Waiting for processing ...", flush=True)
    uploaded = wait_for_file_active(client, uploaded)

    print(f"  Generating summary ...", flush=True)
    response = client.models.generate_content(
        model=MODEL,
        contents=[uploaded, prompt],
    )

    # Clean up uploaded file to free storage quota
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    return response.text


def resolve_prompt(args) -> str:
    """Return custom prompt if provided, otherwise the default."""
    if args.prompt:
        print(f"Using custom inline prompt.")
        return args.prompt
    if args.prompt_file:
        p = pathlib.Path(args.prompt_file)
        if not p.exists():
            print(f"ERROR: Prompt file not found: {p}", file=sys.stderr)
            sys.exit(1)
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            print(f"ERROR: Prompt file is empty: {p}", file=sys.stderr)
            sys.exit(1)
        print(f"Using custom prompt from: {p}")
        return text
    return PROMPT


def main():
    parser = argparse.ArgumentParser(
        description="Summarize MP4 videos using the Gemini API."
    )
    parser.add_argument(
        "directory", nargs="?", default=None,
        help="Directory to scan for MP4 files (default: current directory)"
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

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    scan_dir = pathlib.Path(args.directory) if args.directory else pathlib.Path.cwd()
    if not scan_dir.is_dir():
        print(f"ERROR: Not a directory: {scan_dir}", file=sys.stderr)
        sys.exit(1)

    prompt = resolve_prompt(args)

    from google import genai

    videos = sorted(scan_dir.rglob("*.mp4"))
    if not videos:
        print(f"No MP4 files found in {scan_dir}")
        sys.exit(0)

    print(f"Found {len(videos)} video(s) in {scan_dir}\n")
    client = genai.Client(api_key=api_key)

    success, failed, skipped = 0, 0, 0
    for i, video in enumerate(videos, 1):
        out_path = video.with_suffix(".md")
        prefix = f"[{i}/{len(videos)}] {video.name}"

        if out_path.exists():
            print(f"SKIP  {prefix}  (summary already exists)")
            skipped += 1
            continue

        print(f"\nPROC  {prefix}")
        try:
            summary = summarize_video(client, video, prompt)
            out_path.write_text(summary, encoding="utf-8")
            print(f"  -> Saved: {out_path}")
            success += 1
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            failed += 1

    print(f"\n--- Done: {success} summarized, {skipped} skipped, {failed} failed ---")


if __name__ == "__main__":
    main()
