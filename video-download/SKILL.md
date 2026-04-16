---
name: 	
description: >
  Download videos from Instagram, YouTube, TikTok, Twitter/X, Facebook, and 1000+ other
  platforms as MP4 files using yt-dlp. Use this skill when the user wants to download one
  or more videos from any social media or video platform URL, or asks to "save", "download",
  or "grab" a video. Supports saving to the current working directory or a specified target
  folder. Handles authentication via browser cookies when needed.
---

# Video Download Skill

Download videos from Instagram, YouTube, TikTok, Twitter/X, and 1000+ sites as MP4.

## Tool

**Script:** `scripts/download.py` -- wraps yt-dlp, handles install check, MP4 merging, folder creation.

## Workflow

1. Collect all URLs from the user's request (can be a single URL or a list)
2. Determine the output directory:
   - No folder specified: use the current working directory
   - Folder specified: use it as-is (will be created if missing)
3. Run the download script
4. Report which files were saved and where

## Usage

```bash
# Single video, current directory
python scripts/download.py "https://www.youtube.com/watch?v=..."

# Multiple URLs, specific folder
python scripts/download.py "URL1" "URL2" "URL3" -o "/path/to/output"

# With browser cookies (for private/login-required content)
python scripts/download.py "URL" --cookies-from-browser chrome
```

## Output Filename Pattern

`{uploader}_{video_id}.mp4` -- e.g. `DesignMotion_DUf3nehjIg7.mp4`

## Authentication

If a video requires login (private Instagram posts, age-restricted YouTube, etc.):
- Add `--cookies-from-browser chrome` (or `firefox`, `edge`, `safari`)
- The user must be logged in to that platform in the specified browser

## Supported Platforms (examples)

- YouTube (including playlists -- use `--no-playlist` disabled for full playlists)
- Instagram (posts, reels)
- TikTok
- Twitter / X
- Facebook
- Vimeo
- Reddit
- And 1000+ more via yt-dlp

## Notes

- yt-dlp is auto-installed if not present
- `--no-playlist` is set by default; remove it from the script call for full playlists
- Best quality MP4 is always selected (video + audio merged automatically)
