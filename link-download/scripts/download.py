#!/usr/bin/env python3
"""Download videos (Instagram, YouTube, etc.) as MP4 using yt-dlp."""

import subprocess
import sys
import os


def ensure_yt_dlp():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass
    print("Installing yt-dlp...")
    subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"], check=True)
    return True


def download_videos(urls: list[str], output_dir: str = None, cookies_from_browser: str = None, mp3: bool = False):
    """
    Download videos as MP4 or extract audio as MP3.

    Args:
        urls: List of video URLs
        output_dir: Target directory (default: current working directory)
        cookies_from_browser: Browser name for cookies (e.g. 'chrome', 'firefox')
        mp3: If True, extract audio and convert to MP3
    """
    ensure_yt_dlp()

    if not output_dir:
        output_dir = os.getcwd()

    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, "%(uploader)s_%(id)s.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--output", output_template,
        "--no-playlist",
        "--progress",
    ]

    if mp3:
        cmd += [
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
        ]
    else:
        cmd += [
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
        ]

    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]

    cmd += urls

    fmt = "MP3 audio" if mp3 else "MP4 video"
    print(f"Downloading {len(urls)} {fmt} file(s) to: {output_dir}")
    print("-" * 50)

    result = subprocess.run(cmd)
    return result.returncode == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download videos as MP4")
    parser.add_argument("urls", nargs="+", help="Video URLs to download")
    parser.add_argument("-o", "--output", default=None, help="Output directory (default: current dir)")
    parser.add_argument("--mp3", action="store_true", help="Extract audio as MP3 instead of downloading video")
    parser.add_argument("--cookies-from-browser", default=None,
                        help="Use cookies from browser (chrome/firefox/edge/safari)")

    args = parser.parse_args()

    success = download_videos(
        urls=args.urls,
        output_dir=args.output,
        cookies_from_browser=args.cookies_from_browser,
        mp3=args.mp3,
    )

    sys.exit(0 if success else 1)
