---
name: 	
description: >
  Download videos as MP4 or extract audio as MP3 from Instagram, YouTube, TikTok, Twitter/X,
  Facebook, and 1000+ other platforms using yt-dlp. Use this skill when the user wants to
  download, save, or grab a video or audio/song/music from any URL. Supports MP4 (default)
  and MP3 (with --mp3 flag). Handles authentication via browser cookies when needed.
---

# Video & Audio Download Skill

Download videos as MP4 or extract audio as MP3 from Instagram, YouTube, TikTok, Twitter/X, and 1000+ sites.

## Tool

**Script:** `scripts/download.py` -- wraps yt-dlp, handles install check, MP4 merging, MP3 extraction, folder creation.

## Workflow

1. Collect all URLs from the user's request (can be a single URL or a list)
2. Determine the format:
   - Default: MP4 video
   - If user asks for audio/MP3/song/music: use `--mp3`
3. Determine the output directory:
   - No folder specified: use the current working directory
   - Folder specified: use it as-is (will be created if missing)
4. Run the download script
5. Report which files were saved and where

## Usage

```bash
# Single video as MP4, current directory
python scripts/download.py "https://www.youtube.com/watch?v=..."

# Extract audio as MP3
python scripts/download.py "https://www.youtube.com/watch?v=..." --mp3

# Multiple URLs as MP3 to a specific folder
python scripts/download.py "URL1" "URL2" --mp3 -o "/path/to/output"

# With browser cookies (for private/login-required content)
python scripts/download.py "URL" --cookies-from-browser chrome
```

## Output Filename Pattern

- MP4: `{uploader}_{video_id}.mp4` -- e.g. `DesignMotion_DUf3nehjIg7.mp4`
- MP3: `{uploader}_{video_id}.mp3` -- e.g. `DesignMotion_DUf3nehjIg7.mp3`

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
- MP4: best quality video + audio merged automatically
- MP3: extracts audio and converts to MP3 (192 kbps) via ffmpeg; ffmpeg must be installed
