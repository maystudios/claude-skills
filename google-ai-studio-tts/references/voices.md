# Voices in Gemini Flash TTS (AI Studio)

The voice picker exposes 32 named voices. Each has a character descriptor and a pitch class. List was extracted live from the AI Studio voice drawer. Names are case-sensitive.

## Default pairing (two-host podcast)

| Slot | Voice | Trait | Pitch |
|---|---|---|---|
| Speaker 1 | Puck | Upbeat | Middle pitch |
| Speaker 2 | Zephyr | Bright | Middle pitch |

## Full catalogue (alphabetical)

| Voice | Trait | Pitch |
|---|---|---|
| Achernar | Soft | Higher pitch |
| Achird | Friendly | Lower middle pitch |
| Algenib | Gravelly | Lower pitch |
| Algieba | Smooth | Lower pitch |
| Alnilam | Firm | Lower middle pitch |
| Aoede | Breezy | Middle pitch |
| Autonoe | Bright | Middle pitch |
| Callirrhoe | Easy-going | Middle pitch |
| Charon | Informative | Lower pitch |
| Despina | Smooth | Middle pitch |
| Enceladus | Breathy | Lower pitch |
| Erinome | Clear | Middle pitch |
| Fenrir | Excitable | Lower middle pitch |
| Gacrux | Mature | Middle pitch |
| Iapetus | Clear | Lower middle pitch |
| Kore | Firm | Middle pitch |
| Laomedeia | Upbeat | Higher pitch |
| Leda | Youthful | Higher pitch |
| Orus | Firm | Lower middle pitch |
| Puck | Upbeat | Middle pitch |
| Pulcherrima | Forward | Middle pitch |
| Rasalgethi | Informative | Middle pitch |
| Sadachbia | Lively | Lower pitch |
| Sadaltager | Knowledgeable | Middle pitch |
| Schedar | Even | Lower middle pitch |
| Sulafat | Warm | Middle pitch |
| Umbriel | Easy-going | Lower middle pitch |
| Vindemiatrix | Gentle | Middle pitch |
| Zephyr | Bright | Middle pitch |
| Zubenelgenubi | Casual | Lower middle pitch |

(Two slots are reserved system voices that don't appear here — the drawer is the source of truth if a name shown to the user doesn't appear above.)

## Picking voices by intent

| Intent | Suggested voices |
|---|---|
| Calm narrator (audiobook) | Sulafat, Vindemiatrix, Despina |
| Energetic podcast host | Puck, Laomedeia, Sadachbia |
| Co-host / counterpoint | Zephyr, Autonoe, Callirrhoe |
| News anchor / authoritative | Charon, Rasalgethi, Sadaltager |
| Character with edge | Algenib (gravelly), Fenrir (excitable), Gacrux (mature) |
| Soft / intimate | Achernar, Enceladus (breathy), Leda (youthful) |
| Neutral training / explainer | Erinome, Iapetus, Schedar |

## Director's note (per-speaker)

Each speaker also has a Director's note with three dropdowns. Common values seen in templates:

- **Style:** Vocal Smile, Neutral, Whisper, Confident, Warm
- **Pace:** Rapid Fire, Conversational, Slow, Measured
- **Accent:** American (Gen), British, Indian, Australian, etc.

Plus a free-text **Audio Profile** (e.g. "An authoritative main news anchor.") which is the strongest steering control — use it to capture the role in one sentence.
