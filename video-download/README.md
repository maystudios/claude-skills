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

# Full playlist
py scripts/download.py "https://www.youtube.com/playlist?list=..." --playlist -o "./out"

# Higher quality
py scripts/download.py "URL" --max-height 1080
```

### Arguments

| Argument | Description |
|---|---|
| `urls` (positional) | One or more video URLs |
| `-o`, `--output` | Output directory (default: current working directory) |
| `--max-height` | Max video height in pixels (default: 720) |
| `--playlist` | Download full playlist (default: single-video mode) |
| `--cookies-from-browser` | Pull cookies from browser: `chrome`, `firefox`, `edge`, `brave`, etc. |
| `--cookies` | Force a specific cookies.txt file |
| `--no-archive` | Disable resume tracking |

## Output

Files are saved using these naming patterns:

- **Single video:** `{title} [{id}].mp4`
- **Playlist:** `{NNN} - {title} [{id}].mp4` (zero-padded, sorts correctly)

## Auto-Recovery from YouTube Bot Detection

The script automatically rotates through strategies when YouTube blocks the download:

1. No auth + throttle (default)
2. Player client rotation (`tv`, `mweb`, `web_safari`)
3. Browser cookie rotation (tries installed browsers: Chrome → Edge → Firefox → Brave → ...)
4. Cookies file discovery (picks newest `.txt` file from `~/Downloads/`)

If all strategies fail, the script prints step-by-step recovery instructions.

## Resume Safety

Downloads use a `.download-archive.txt` file by default. Already-downloaded videos
are skipped on re-runs — safe to restart after interruptions or add more URLs.

## Supported Platforms

| Platform | Notes |
|---|---|
| YouTube | Single videos + playlists |
| Instagram | Posts, Reels |
| TikTok | |
| Twitter / X | |
| Facebook | |
| Vimeo | |
| Reddit | |
| 1000+ more | Full list: [yt-dlp Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |

## Authentication

For private or login-required content:

1. Log in to the platform in your browser
2. Pass `--cookies-from-browser chrome` (or `firefox`, `edge`, etc.)

On Windows with Chrome 127+, Chrome must be **closed** for cookie access (App-Bound Encryption).
Alternatively, export cookies via the "Get cookies.txt LOCALLY" extension and drop the file in `~/Downloads/`.

## File Structure

```
video-download/
  SKILL.md              # Claude skill configuration
  scripts/
    download.py         # Main script (yt-dlp wrapper with auto-recovery)
  README.md
```
