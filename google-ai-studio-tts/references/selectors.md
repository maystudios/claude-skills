# DOM selectors and Angular gotchas

The AI Studio playground is an Angular app. These selectors were verified live against `https://aistudio.google.com/generate-speech`. They are stable enough for automation but Google can change them — if any selector returns null, fall back to `find` (natural-language search) before failing.

## Mode toggle (top-right of playground)

```js
// Two buttons: "Text" and "Composer"
document.querySelectorAll('button.toggle-button')
// Active one carries class `ms-button-active`
```

To switch:

```js
[...document.querySelectorAll('button.toggle-button')]
  .find(b => b.innerText.trim().endsWith('Composer'))?.click();
```

## Shared fields (both modes)

| Field | Selector |
|---|---|
| Scene | `textarea[aria-label="Scene"]` |
| Sample Context | `textarea[aria-label="Sample Context"]` |

## Text mode

| Field | Selector |
|---|---|
| Single prompt | `textarea[aria-label="Enter a prompt"]` |

## Composer mode

| Element | Selector | Notes |
|---|---|---|
| Speech-block textareas | `textarea[aria-label="Speech block text"]` | One per block, indexed in DOM order. |
| Per-block voice chip | `button.voice-chip.ms-button-filter-chip` | Text reads `Speaker N - VoiceName`. Click to reassign. |
| Add new block | `button.add-speech-block-button` | Inherits previous speaker. |

## Right-side panels

| Element | Selector |
|---|---|
| Run settings — Get code | `button[aria-label="Get code"]` |
| Model settings expander | `h4` / `.section-title` containing `Model settings` |
| Temperature value input | `input.slider-number-input` near label "Temperature" (range 0–2) |
| Speaker card (each) | `ms-voice-settings` |
| Active speaker card | `.active-voice-card` |

Click any speaker card to open the voice picker drawer. Inside the drawer:

| Element | Selector |
|---|---|
| Voice search box | `input[placeholder*="Search voices"]` |
| Each voice row | A clickable `mat-list-item`-like container — match by inner text on the voice name. |
| Style / Pace / Accent dropdowns | `mat-select` triggers under "Director's note" |
| Audio Profile field | A textarea inside the drawer right after "Audio Profile" heading |
| Close drawer | The `×` icon in the drawer header |

## Run / playback bar (bottom)

| Element | Selector |
|---|---|
| Run | `button.ctrl-enter-submits` (also reachable via `Ctrl+Enter`) |
| Play / pause | The leftmost icon button on the bottom bar |
| Download | The cloud-arrow icon button on the bottom bar |
| Duration counter | `0:00 / X:XX` text node next to the seek slider |

## Setting Angular textareas correctly

Plain assignment (`el.value = "..."`) does not flow into Angular's reactive form. Use this helper:

```js
function setNgInputValue(el, value) {
  const proto = Object.getPrototypeOf(el);
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set
              || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(el, value);
  el.dispatchEvent(new Event('input',  { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.dispatchEvent(new Event('blur',   { bubbles: true }));
}

setNgInputValue(document.querySelector('textarea[aria-label="Scene"]'),
                'A quiet kitchen, morning light, minimal reverb.');
```

The MCP `form_input` tool already does the right thing — prefer it when you have a `ref` from `find` or `read_page`. Drop to this helper only when you need to set many fields at once or want one batched JS call.

## Detecting render completion

After clicking Run, the audio player at the bottom updates its right-hand duration counter from `0:00` to the actual length. Poll this rather than time-based waits:

```js
function isReady() {
  const t = document.querySelector('.seek-slider')?.parentElement?.innerText || '';
  // matches "0:00 / 0:26"
  const m = t.match(/(\d+):(\d{2})\s*\/\s*(\d+):(\d{2})/);
  if (!m) return false;
  const total = (+m[3]) * 60 + (+m[4]);
  return total > 0;
}
```

## Common breakage modes

- **Banner overlays cover the Run button.** Close any AI Studio banner (`button[aria-label="Close ..."]` or the `×` glyph in the banner) before clicking Run.
- **Form value snaps back.** You used `el.value = ...` without dispatching events — switch to `setNgInputValue` or `form_input`.
- **Speaker chip click does nothing.** The chip opens a popover one frame later — wait one tick, then look for the popover's `ms-voice-settings` element to confirm it's open.
- **Voice list is empty after opening.** The drawer lazy-loads on first open; wait ~200 ms or call `read_page` to force a reflow.
