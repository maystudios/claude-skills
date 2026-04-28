#!/usr/bin/env python3
"""Download videos (Instagram, YouTube, etc.) as MP4 using yt-dlp.

Auto-recovers from YouTube bot-detection ("Sign in to confirm you're not a bot",
LOGIN_REQUIRED) by rotating through a strategy chain — no manual intervention
needed in most cases.
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BOT_PATTERNS = [
    r"Sign in to confirm.*not a bot",
    r"LOGIN_REQUIRED",
    r"Failed to extract any player response",
    r"Requested format is not available",  # sometimes a downstream of bot block
]

# Strategy-specific failures: this strategy can't run on this machine right now,
# but it's not a content-side error. Try the next strategy.
STRATEGY_FAILURE_PATTERNS = [
    r"Could not copy .* cookie database",
    r"Failed to decrypt with DPAPI",
    r"could not find .* cookies database",
    r"is not currently supported",
    r"Permission denied",
    r"Could not find a usable .* profile",
]

COOKIE_FILE_GLOBS = [
    "~/Downloads/www.youtube.com_cookies.txt",
    "~/Downloads/youtube.com_cookies.txt",
    "~/Downloads/youtube*cookies*.txt",
    "~/Downloads/cookies.txt",
    "~/youtube_cookies.txt",
    "~/cookies.txt",
]

BROWSER_PRIORITY = ["chrome", "edge", "firefox", "brave", "vivaldi", "opera"]


def ensure_yt_dlp():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return
    except Exception:
        pass
    print("Installing yt-dlp...", flush=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "yt-dlp"], check=True)


def looks_like_bot_block(stderr: str) -> bool:
    return any(re.search(p, stderr, re.IGNORECASE) for p in BOT_PATTERNS)


def looks_like_strategy_failure(stderr: str) -> bool:
    """Strategy can't run on this machine (locked cookie DB, DPAPI fail, ...).
    Not the content's fault — try the next strategy."""
    return any(re.search(p, stderr, re.IGNORECASE) for p in STRATEGY_FAILURE_PATTERNS)


def find_cookies_file(max_age_hours: float = 168.0) -> str | None:
    """Return newest cookies file from common locations, if fresh enough."""
    candidates: list[tuple[float, str]] = []
    for pat in COOKIE_FILE_GLOBS:
        for match in glob.glob(os.path.expanduser(pat)):
            if os.path.isfile(match) and os.path.getsize(match) > 100:
                candidates.append((os.path.getmtime(match), match))
    if not candidates:
        return None
    mtime, path = max(candidates)
    age_hours = (time.time() - mtime) / 3600
    if age_hours > max_age_hours:
        print(f"  (found cookies file {path} but it's {age_hours:.1f}h old — likely stale)", flush=True)
        return None
    return path


def browser_available(browser: str) -> bool:
    """Heuristic: does this browser have a profile dir on the system?"""
    home = Path.home()
    paths = {
        "chrome": [home / "AppData/Local/Google/Chrome/User Data",
                   home / ".config/google-chrome",
                   home / "Library/Application Support/Google/Chrome"],
        "edge": [home / "AppData/Local/Microsoft/Edge/User Data",
                 home / ".config/microsoft-edge",
                 home / "Library/Application Support/Microsoft Edge"],
        "firefox": [home / "AppData/Roaming/Mozilla/Firefox/Profiles",
                    home / ".mozilla/firefox",
                    home / "Library/Application Support/Firefox/Profiles"],
        "brave": [home / "AppData/Local/BraveSoftware/Brave-Browser/User Data",
                  home / ".config/BraveSoftware/Brave-Browser",
                  home / "Library/Application Support/BraveSoftware/Brave-Browser"],
        "vivaldi": [home / "AppData/Local/Vivaldi/User Data",
                    home / ".config/vivaldi"],
        "opera": [home / "AppData/Roaming/Opera Software/Opera Stable",
                  home / ".config/opera"],
    }
    return any(p.exists() for p in paths.get(browser, []))


def build_cmd(urls, *, output_template, format_sel, archive_path,
              cookies_browser=None, cookies_file=None, throttle=True,
              player_clients=None, no_playlist=True, extra_args=()):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--output", output_template,
        "--format", format_sel,
        "--merge-output-format", "mp4",
        "--windows-filenames",
        "--no-overwrites",
        "--continue",
        "--ignore-errors",
        "--no-warnings",
        "--retries", "10",
        "--fragment-retries", "10",
        "--concurrent-fragments", "4",
    ]
    if no_playlist:
        cmd.append("--no-playlist")
    if archive_path:
        cmd += ["--download-archive", archive_path]
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    if cookies_file:
        cmd += ["--cookies", cookies_file]
    if throttle:
        cmd += ["--sleep-requests", "1",
                "--sleep-interval", "2",
                "--max-sleep-interval", "5"]
    if player_clients:
        cmd += ["--extractor-args", f"youtube:player_client={player_clients}"]
    cmd += list(extra_args)
    cmd += list(urls)
    return cmd


def run_strategy(label: str, cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"\n>> Strategy: {label}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    sys.stdout.flush()
    return proc


def build_strategy_chain(forced_cookies_browser=None, forced_cookies_file=None):
    """Return a list of (label, kwargs) tuples to try in order."""
    if forced_cookies_browser:
        return [(f"forced cookies-from-{forced_cookies_browser}",
                 {"cookies_browser": forced_cookies_browser})]
    if forced_cookies_file:
        return [(f"forced cookies-file ({forced_cookies_file})",
                 {"cookies_file": forced_cookies_file})]

    chain = [
        # Tier 0: no auth, throttled, default clients
        ("no-auth + throttle", {}),
        # Tier 1: rotate player clients (sometimes bypasses block)
        ("no-auth + tv,mweb,web_safari clients",
         {"player_clients": "default,tv,mweb,web_safari"}),
    ]
    # Tier 2: rotate browser cookies (only browsers actually installed)
    for browser in BROWSER_PRIORITY:
        if browser_available(browser):
            chain.append((f"cookies-from-{browser}",
                         {"cookies_browser": browser}))
    # Tier 3: manual cookies file (newest fresh one in common locations)
    cookies_file = find_cookies_file()
    if cookies_file:
        chain.append((f"cookies-file: {cookies_file}",
                     {"cookies_file": cookies_file}))
    return chain


def download_videos(urls, output_dir=None, max_height=720, no_playlist=False,
                    cookies_from_browser=None, cookies_file=None,
                    archive=True):
    """Download videos with auto-recovery on bot detection."""
    ensure_yt_dlp()

    output_dir = output_dir or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(
        output_dir,
        "%(playlist_index& - |)s%(playlist_index)s%(playlist_index& - |)s%(title).100B [%(id)s].%(ext)s"
    )
    # If no playlist, drop the playlist_index prefix:
    if no_playlist:
        output_template = os.path.join(output_dir, "%(title).100B [%(id)s].%(ext)s")

    archive_path = os.path.join(output_dir, ".download-archive.txt") if archive else None
    fmt = (f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]"
           f"/bv*[height<={max_height}]+ba"
           f"/b[height<={max_height}]")

    chain = build_strategy_chain(cookies_from_browser, cookies_file)
    cookie_file_present = any("cookies-file" in label for label, _ in chain)

    print(f"Output: {output_dir}", flush=True)
    print(f"Format: <={max_height}p MP4", flush=True)
    print(f"Archive: {archive_path or 'disabled'}", flush=True)
    print(f"Strategies queued: {len(chain)}", flush=True)

    last_proc = None
    cookie_file_was_rejected = False
    for label, kwargs in chain:
        cmd = build_cmd(
            urls,
            output_template=output_template,
            format_sel=fmt,
            archive_path=archive_path,
            no_playlist=no_playlist,
            **kwargs,
        )
        proc = run_strategy(label, cmd)
        last_proc = proc

        if proc.returncode == 0:
            print(f"\n[OK] Strategy '{label}' succeeded.", flush=True)
            return 0

        stderr = proc.stderr or ""
        if looks_like_strategy_failure(stderr):
            print(f"  Strategy '{label}' couldn't run on this machine - trying next.", flush=True)
            continue
        if looks_like_bot_block(stderr):
            if "cookies-file" in label:
                cookie_file_was_rejected = True
            print(f"  Bot detection on '{label}' - trying next strategy.", flush=True)
            continue

        # Definitive failure (network, format, 404, ...) - stop rotating
        print(f"\n[FAIL] Strategy '{label}' failed (not bot/strategy issue) - stopping.", flush=True)
        return proc.returncode

    print_recovery_instructions(cookie_file_present, cookie_file_was_rejected)
    return last_proc.returncode if last_proc else 1


def print_recovery_instructions(cookie_file_present: bool, cookie_file_rejected: bool) -> None:
    """Print a step-by-step guide for the user to unblock the download.

    Three flavors based on what just happened:
    - cookies file existed but was rejected -> stale, re-export NOW
    - cookies file missing -> first-time setup walkthrough
    - cookies file optional -> short list (Chrome close, wait, etc.)
    """
    line = "=" * 70
    print(f"\n{line}", flush=True)
    print("[EXHAUSTED] All strategies failed. YouTube has bot-blocked this IP.",
          flush=True)
    print(line, flush=True)

    if cookie_file_rejected:
        print("\nA cookies file was found but rejected - it's stale or invalid.",
              flush=True)
        print("YouTube cookies expire fast once a bot-block triggers.\n", flush=True)
        print("FIX: Re-export fresh cookies RIGHT NOW (takes 30 seconds):", flush=True)
        _print_cookie_export_steps()
    elif not cookie_file_present:
        print("\nNo cookies file found. Easiest fix:\n", flush=True)
        print("FIX: Export YouTube cookies via a browser extension.", flush=True)
        _print_cookie_export_steps()
    else:
        print("", flush=True)

    print("\nALTERNATIVES:", flush=True)
    print("  - Close your browser completely. The script will read its cookie", flush=True)
    print("    store directly on the next run (no extension needed).", flush=True)
    print("    On Windows + Chrome 127+, the browser MUST be closed because of", flush=True)
    print("    App-Bound Encryption locking the cookie database.", flush=True)
    print("  - Wait several hours. YouTube IP blocks lift on their own,", flush=True)
    print("    typically within 24h.", flush=True)
    print("  - Use a different network (mobile hotspot, VPN) - new IP, no block.",
          flush=True)
    print(line, flush=True)


def _print_cookie_export_steps() -> None:
    """Print the cross-browser cookie export walkthrough."""
    print("", flush=True)
    print("  1. Install a cookie export extension:", flush=True)
    print("     - Chrome / Edge / Brave: 'Get cookies.txt LOCALLY'", flush=True)
    print("       https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc",
          flush=True)
    print("     - Firefox: 'cookies.txt'", flush=True)
    print("       https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/",
          flush=True)
    print("", flush=True)
    print("  2. Open https://www.youtube.com in that browser. Make sure you", flush=True)
    print("     are signed in to your Google account.", flush=True)
    print("", flush=True)
    print("  3. Click the extension's icon in the toolbar.", flush=True)
    print("     - 'Get cookies.txt LOCALLY': click 'Export As' -> Netscape format,", flush=True)
    print("       use the 'Current Site' option so only youtube.com cookies are", flush=True)
    print("       included.", flush=True)
    print("     - Firefox 'cookies.txt': click 'Current Site' -> Save.", flush=True)
    print("", flush=True)
    print("  4. Save the file to your Downloads folder. Any of these names work:", flush=True)
    print("       www.youtube.com_cookies.txt   (extension's default)", flush=True)
    print("       youtube.com_cookies.txt", flush=True)
    print("       cookies.txt", flush=True)
    print("", flush=True)
    print("  5. Re-run the same download command. The script auto-detects the", flush=True)
    print("     newest cookies file in Downloads (within the last 7 days).", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Download videos as MP4 with auto-recovery on bot detection.",
    )
    parser.add_argument("urls", nargs="+", help="Video / playlist URLs")
    parser.add_argument("-o", "--output", default=None,
                        help="Output directory (default: current dir)")
    parser.add_argument("--max-height", type=int, default=720,
                        help="Max video height in pixels (default: 720)")
    parser.add_argument("--playlist", action="store_true",
                        help="Download full playlist (default: single-video mode)")
    parser.add_argument("--cookies-from-browser", default=None,
                        help="Force a specific browser (chrome/edge/firefox/brave/...). "
                             "Skips auto-rotation.")
    parser.add_argument("--cookies", default=None,
                        help="Force a specific cookies.txt file. Skips auto-rotation.")
    parser.add_argument("--no-archive", action="store_true",
                        help="Disable download-archive (default: enabled, "
                             "lets you resume by re-running the same command)")

    args = parser.parse_args()

    sys.exit(download_videos(
        urls=args.urls,
        output_dir=args.output,
        max_height=args.max_height,
        no_playlist=not args.playlist,
        cookies_from_browser=args.cookies_from_browser,
        cookies_file=args.cookies,
        archive=not args.no_archive,
    ))


if __name__ == "__main__":
    main()
