# video-fetch-and-summarize

A Claude Code skill that downloads videos from URLs and generates a Markdown summary for each one — all in a single step. Each video is saved in its own subfolder containing the MP4 file and a `summary.md`.

Combines video downloading (yt-dlp) and AI summarization (Gemini API) into one fully self-contained skill.

## Installation

### 1. Get a Gemini API key

Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) and create a free API key.

### 2. Set the environment variable

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

**Windows (persistent via System Settings):**
Search for "Environment Variables" in the Start Menu and add `GEMINI_API_KEY` as a user variable.

**macOS / Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Add it to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### 3. Install the skill in Claude Code

Python dependencies (`yt-dlp`, `google-genai`) are installed automatically on first run.

## Usage

Once the skill is active, tell Claude:

> "Download and summarize these videos: URL1, URL2"
> "Process this list of Instagram links and summarize each one"
> "Here's my links.md — download and summarize everything in it"

Claude will run the script automatically.

### Run the script directly

```bash
# Direct URLs
py scripts/fetch_and_summarize.py "https://instagram.com/..." "https://youtube.com/..." -o ./output

# From a TXT file with one URL per line
py scripts/fetch_and_summarize.py links.txt -o ./output

# From a Markdown file (URLs are extracted automatically)
py scripts/fetch_and_summarize.py links.md -o ./output

# Mix of direct URLs and files
py scripts/fetch_and_summarize.py "https://..." notes.md -o ./output

# Private or login-required content
py scripts/fetch_and_summarize.py links.txt --cookies-from-browser chrome -o ./output
```

### Arguments

| Argument | Description |
|---|---|
| `sources` (positional) | Video URLs and/or paths to text files containing URLs |
| `-f`, `--file` | Explicitly pass a file with URLs (repeatable) |
| `-o`, `--output` | Base output directory (default: current working directory) |
| `--cookies-from-browser` | Pull cookies from browser: `chrome`, `firefox`, `edge`, `safari` |

## Output Structure

```
output/
  First_Video_Title/
      DesignMotion_DUf3nehjIg7.mp4
      summary.md
  Second_Video_Title/
      Profaura_DUBJOtMDGsT.mp4
      summary.md
  ...
```

Folder names are derived from the video title (max 80 characters, special characters replaced).

## Summary Format

```markdown
# [Video Title]

## Summary
[2-3 sentence description of the video and its main topic]

## Key Points
- Key point 1
- Key point 2
- ...

## Core Content & Takeaways
[Central message and most important insight, 2-4 sentences]

---
*Auto-generated with Gemini API*
```

The summary language automatically matches the language spoken or shown in the video.

## Supported Platforms

YouTube, Instagram (Posts/Reels), TikTok, Twitter/X, Facebook, Vimeo, Reddit, and 1000+ more via yt-dlp.

## Behavior

- **Idempotent**: Videos where both the MP4 and `summary.md` already exist are skipped on re-runs
- **503 errors**: If Gemini is overloaded, just re-run the script — completed videos are skipped automatically
- **URL extraction**: Works with any text format — URLs are found via regex, no special formatting required

## Model

`gemini-3-flash-preview` — configurable in `scripts/fetch_and_summarize.py` (line `GEMINI_MODEL = ...`)

## File Structure

```
video-fetch-and-summarize/
  SKILL.md                      # Claude skill configuration
  scripts/
    fetch_and_summarize.py      # Main script (yt-dlp + Gemini combined)
  README.md
```
