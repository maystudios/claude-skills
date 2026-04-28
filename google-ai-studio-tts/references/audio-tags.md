# Inline audio tags & speaker prefixes

Gemini Flash TTS responds to two kinds of in-script directives.

## Speaker prefixes

Place at the start of a line in **Text mode**. Composer sets the speaker via the chip — don't add the prefix there.

```
Speaker 1: hello there.
Speaker 2: hi back.
```

`Speaker 1`, `Speaker 2`, … map to slot 1, 2, … in the right-hand Speaker settings panel. The voice for each slot is whatever was selected for it.

## Inline emotion / delivery tags

Bracketed tags placed inside a line steer the delivery of the words that follow them. Tags are not spoken. Stack at most one tag per logical clause.

| Category | Tags (examples) |
|---|---|
| Mood | `[enthusiastic]`, `[sad]`, `[angry]`, `[amazed]`, `[bored]`, `[anxious]`, `[curious]`, `[empathy]` |
| Vocal mode | `[whispers]`, `[shouts]`, `[mumbles]`, `[singing]`, `[breathy]` |
| Reactions | `[laughs]`, `[laughter]`, `[chuckles]`, `[sighs]`, `[gasps]`, `[clears throat]` |
| Pacing | `[slow]`, `[fast]`, `[rapid fire]`, `[pauses]` |
| Tone | `[warm]`, `[cold]`, `[sarcastic]`, `[serious]`, `[playful]`, `[skeptical]` |
| Beats | `[agreement]`, `[animation]`, `[amazement]`, `[realisation]`, `[hesitation]` |

Examples (lifted from the AI Studio "Energetic Co-Host" template):

```
Speaker 1: [enthusiastic] Welcome back to the show! Today we're diving in.
Speaker 2: [agreement] Exactly. I've got so many thoughts on this week.
Speaker 1: [animation] It really is shifting daily.
Speaker 2: [amazement] Oh, absolutely. It blew my mind! [laughter]
```

## Where the heavy steering actually lives

Inline tags handle line-by-line emotion. For the **overall feel**, push hardest on:

1. **Audio Profile** in the speaker drawer ("An authoritative main news anchor."). One sentence. Strongest control.
2. **Director's note**: Style + Pace + Accent (three dropdowns).
3. **Scene** (acoustic environment).
4. **Sample Context** (delivery tone reference).

Inline tags then nudge individual moments. Don't try to express "this whole podcast is energetic" purely with tags — set the Director's note to Rapid Fire / Vocal Smile and let tags do the per-line variation.

## Pitfalls

- Tags are case-sensitive in some templates. Stick to lowercase: `[laughs]`, not `[LAUGHS]`.
- Compound tags (`[enthusiastic and fast]`) are unreliable — split into two tags or pick one.
- Parenthetical stage directions (`(she sighs)`) may be **read aloud**. Always use brackets `[…]` for non-spoken directives.
- Tags only steer the line they're on. Re-tag every line that needs a specific delivery.
