# video-summarizer

A Claude Code skill that analyzes MP4 video files using the Gemini API and generates a structured Markdown summary for each video — saved right next to the original file.

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

### 3. Install the Python dependency

```bash
pip install google-genai
```

### 4. Install the skill in Claude Code

## Usage

Once the skill is active, tell Claude:

> "Summarize all the videos in this folder"
> "Create Markdown summaries for my videos"
> "Analyze the videos in C:/Videos with Gemini"

Claude will run the summarization script automatically.

### Run the script directly

```bash
# Summarize all videos in the current directory (recursive)
py scripts/summarize_videos.py

# Summarize videos in a specific folder
py scripts/summarize_videos.py "C:/Users/you/Downloads/videos"
```

## Summary Format

Each video gets a `<videoname>.md` file in the same folder:

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

## Behavior

- **Idempotent**: Videos that already have a `.md` file next to them are skipped — safe to re-run after interruptions
- **Auto-cleanup**: Uploaded files are deleted from Gemini storage immediately after processing
- **503 errors**: If Gemini is overloaded, just re-run the script — completed videos are skipped automatically

## Model

`gemini-3-flash-preview` — configurable in `scripts/summarize_videos.py` (line `MODEL = ...`)

## File Structure

```
video-summarizer/
  SKILL.md                  # Claude skill configuration
  scripts/
    summarize_videos.py     # Main script (Gemini API wrapper)
  README.md
```
