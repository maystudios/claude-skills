# video-download

A Claude Code skill that downloads videos from Instagram, YouTube, TikTok, Twitter/X, Facebook, and 1000+ other platforms as MP4 files — powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Installation

1. Install the skill in Claude Code
2. Make sure Python is available (`py` on Windows, `python3` on macOS/Linux)

No API key required. `yt-dlp` is installed automatically on first run.

## Usage

Once the skill is active, just tell Claude:

> "Download this video: https://..."
> "Save these videos to my Downloads folder: URL1, URL2"
> "Grab this Instagram reel"

Claude will run the download script automatically.

### Run the script directly

```bash
# Single video, current directory
py scripts/download.py "https://www.youtube.com/watch?v=..."

# Multiple URLs, specific output folder
py scripts/download.py "URL1" "URL2" "URL3" -o "/path/to/output"

# Private or login-required content (uses browser cookies)
py scripts/download.py "https://instagram.com/..." --cookies-from-browser chrome
```

### Arguments

| Argument | Description |
|---|---|
| `urls` (positional) | One or more video URLs |
| `-o`, `--output` | Output directory (default: current working directory) |
| `--cookies-from-browser` | Pull cookies from browser: `chrome`, `firefox`, `edge`, `safari` |

## Output

Files are saved using this naming pattern:

```
{uploader}_{video_id}.mp4
```

Example: `DesignMotion_DUf3nehjIg7.mp4`

## Supported Platforms

| Platform | Notes |
|---|---|
| YouTube | Playlists supported (disabled by default) |
| Instagram | Posts, Reels |
| TikTok | |
| Twitter / X | |
| Facebook | |
| Vimeo | |
| Reddit | |
| 1000+ more | Full list: [yt-dlp Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |

## Authentication

For private or login-required content (e.g. private Instagram posts, age-restricted YouTube videos):

1. Log in to the platform in your browser
2. Pass `--cookies-from-browser chrome` (or `firefox`, `edge`, `safari`)

## File Structure

```
video-download/
  SKILL.md              # Claude skill configuration
  scripts/
    download.py         # Main script (yt-dlp wrapper)
  README.md
```
