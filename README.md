# swaylock

## Overview

Configuration and launch tooling for [swaylock-effects](https://github.com/mortie/swaylock-effects), the screen locker. Combines swaylock-effects' native live clock + auth styling (`config`) with a custom Python/Cairo compositor (`wallpaper.py`) that draws the Imperator-graded *Pandemonium* backdrop and a retrofuturist amber-CRT HUD panel, invoked through `lock.sh`.

## Design Philosophy

- **Split of responsibilities: baked HUD vs. live indicator.** `wallpaper.py` bakes everything static — the backdrop, the frosted-glass HUD panel, the House crest and the epitaph — into the `--image`. swaylock-effects renders what must update: the live `HH:MM:SS` clock and a traditional ring password indicator around it, centered on the panel. The ring highlights as you type and changes **colour** for each state — idle Warm Ochre, verifying Signal Blue, wrong Plasma-Red, caps-lock Solar Flare — while the status *text* (verifying / wrong / cleared / caps-lock words) is suppressed, so state reads without messages cluttering the HUD.
- **Retrofuturist HUD, hard-cornered.** The panel is a sharp-edged amber-CRT readout: a real frosted-glass field (cheap cairo down/upscale blur of the backdrop + smoked-amber tint) laced with scanlines, targeting-reticle corner brackets, instrument tick rows, and a terminal-style block-cursor prompt — the "strategic imperial terminal", not a decorative frame.
- **Painting as background, regraded to the palette.** The lock art is John Martin's *Pandemonium* (1841), recolored into the Imperator palette: the colonnaded palace reads amber/gold, the lake of fire keeps the reserved Plasma-Red (`#FF6B2B` family) danger accent, and the sky sinks into Deep Void. The regrade is a duotone/tritone luminance map (Deep Void → Amber Pulse → Golden Signal) blended over a warm base so diffuse detail (crowds, distant architecture, Satan on the promontory) survives rather than crushing into the background. The painting itself is never repainted — every treatment is a color grade / filter pass layered on top.
- **Aged-codex filter pass.** The deployed runtime background (`assests/pandemonium.png`) adds an "illuminated manuscript / old book page" treatment on top of the clean grade: a warm sepia unification, a lifted deep-sepia shadow floor (paper does not go pure black), a soft veiling glow + highlight bloom, a procedural parchment texture (plasma mottle + fine fiber grain) overlaid, a warm — deliberately non-crushing — burnt-edge vignette, and film grain. It reads as aged vellum without leaving the amber/obsidian palette or losing the painting's diffuse detail. The un-aged clean grade remains available as `pandemonium.jpg` for a one-line switch (see Customization).
- **Graceful procedural fallback.** If the painting asset is missing, `wallpaper.py` falls back to a fully Cairo-drawn "tactical map" background (micro-grid, radial perspective lines, golden-ratio structural lines, sparse data-node dots seeded with `random.seed(0xC8960C)` for reproducibility) so the lock flow never breaks.
- **Ephemeral generated assets.** `lock.sh` writes the composited PNG to `/tmp/imperator-lock.png` and (when not daemonized) deletes it after swaylock exits — the rendered lock image is never persisted or committed.
- **Indicator = output center, sized by a shared contract.** The clock+ring sit at swaylock-effects' default position (output center), so `lock.sh` passes **no** `--indicator-x/y-position` (those are offsets-from-center and would push it off). `wallpaper.py` centers its layout on the same point (`clock_center()` = `(W/2, H/2)`); `lock.sh` scales `--font-size`/`--indicator-radius`/`--indicator-thickness` to the resolution so the real ring matches the baked panel.

## Key Features

- Retrofuturist amber-CRT HUD panel: hard-cornered frosted glass (real blur), scanlines, reticle brackets, the House Ziegler crest, and the House epitaph *Leoni Nvlla Vis Avrae*.
- Imperator-graded, aged *Pandemonium* backdrop cover-fit to the output size (center-crop), seated with a warm edge burn.
- Live ticking `HH:MM:SS` clock inside a traditional ring password indicator, both rendered by swaylock-effects at panel center.
- Per-state feedback by ring colour (idle / verifying / wrong / cleared / Caps Lock) with the status text suppressed — no message words on screen.
- Configurable output resolution via `IMPERATOR_LOCK_SIZE` (default `1920x1080`); crest/prompt/epitaph scale with height.

## Configuration Breakdown

| File | Responsibility | Why it exists |
|---|---|---|
| `config` | swaylock-effects settings: `clock` + `timestr=%H:%M:%S` live time, visible ring indicator with per-state ring colours, transparent state *text* (no message words), layout box, font | The dynamic surface — ticking clock + traditional ring auth feedback |
| `wallpaper.py` | Standalone Cairo/PyCairo script that draws the backdrop + retrofuturist HUD panel (frosted glass, scanlines, brackets, crest, prompt, epitaph), leaving the clock slot for swaylock; `--preview-clock` bakes a sample time; procedural fallback if the backdrop asset is missing | Produces everything swaylock cannot: arbitrary art, panel, crest, epitaph |
| `lock.sh` | Orchestration: generates the lock image to `/tmp`, calls `swaylock --image ... --scaling fill` with resolution-scaled `--font-size`/`--indicator-radius`/`--indicator-thickness`, forwards extra args (e.g. `-f`), cleans up | Single entry point wlogout / niri `Mod+Alt+L` / swayidle all call |
| `assests/shield.png` | House Ziegler crest (black keyed to transparent, gold lion + shield outline on glass) — the panel emblem | Derived from `Ziegler.png`; loaded by `wallpaper.py` |
| `assests/Ziegler.png` | Original full-resolution crest (gold-on-black) | Source for `shield.png` |
| `assests/pandemonium.png` | Runtime background `wallpaper.py` loads, at 2880px wide — currently derived from the **aged-codex** master (PNG, so Cairo reads it with no extra dependency) | The actual lock/desktop backdrop |
| `assests/pandemonium-aged.jpg` | Full-resolution (4312×2880) aged-codex master (clean grade + parchment/sepia/glow/vignette/grain) | Human-viewable master; source for the runtime PNG |
| `assests/pandemonium.jpg` | Full-resolution (4312×2880) **clean** Imperator grade, no aging | Alternate look; re-derivation source for both the aged master and a non-aged runtime |
| `assests/pandemonium-original.jpg` | Untouched original scan of the painting | Backup / source for re-running the grade |

## Dependencies

- `swaylock-effects` — `pacman -S swaylock-effects` (cachyos repo). Provides the live `--clock`/`--timestr` and effects the mainline `swaylock` lacks; it supplies the `swaylock` binary, so `config`/`lock.sh` are unchanged. Mainline `swaylock` will **fail** on this `config` (unknown `clock`/`timestr` keys).
- `python3` with the `cairo` (PyCairo) bindings — `pacman -S python-cairo`. Assets ship as PNG so Cairo loads them natively — no image library needed at lock time.
- `bash` — `lock.sh` orchestration.
- ImageMagick (`magick`) is **only** needed to *re-derive* the graded painting or re-key the crest, not to run the lock.
- Optional: `ttf-cinzel` (AUR) for a Roman-inscription epitaph; falls back to Noto Serif.

## Usage

Invoked via `lock.sh` everywhere: niri's `Mod+Alt+L` bind, wlogout's `lock` button, and swayidle (idle-lock at 30 min / before-sleep). Calling `swaylock` bare skips the whole themed HUD and — with this effects-only `config` — fails to start, so always go through `lock.sh`.

## Customization

- **Clock / auth colors**: edit `config` directly — every color is `rrggbbaa` hex without a leading `#`. `text-color` is the clock; `ring-*-color` set the per-state ring (idle / ver / wrong / clear / caps-lock). Keep the `text-*-color` state keys transparent (`00000000`) to suppress the status words; `key-hl-color` is the per-keystroke highlight.
- **HUD panel**: `draw_panel()` in `wallpaper.py` — panel size (`pw`/`ph`), crest height, bracket size, scanline gap, tick counts, and the section Y offsets. All scale by `s = H/1080`.
- **Crest**: swap `assests/shield.png` (re-key from a new source with `magick SRC -fuzz 14% -transparent '#000000' -trim +repage -resize x480 shield.png`).
- **Epitaph / prompt text**: the `tracked_text(...)` calls at the bottom of `draw_panel()`.
- **Clock/ring size**: the base sizes live in `lock.sh` (`FS`/`R`/`TH`, scaled by `H/1080`) and are mirrored by `wallpaper.py`'s layout (crest/epitaph offsets and the preview mock-ring radius) — change both together so the real ring keeps clearing the crest and epitaph.
- **Background image / framing**: swap `assests/pandemonium.png` for any other PNG; `draw_pandemonium()` cover-fits it with an edge burn. `draw_procedural()` is the assetless fallback.
- **Clean vs. aged look**: `pandemonium.png` (what the script loads) is regenerated from whichever master you prefer — `magick pandemonium-aged.jpg -resize 2880x -strip pandemonium.png` for the aged-codex look, or `magick pandemonium.jpg -resize 2880x -strip pandemonium.png` for the clean grade. No code change needed.
- **Re-deriving the clean grade**: the painting is regraded with ImageMagick — a tritone luminance ramp (`#0E0C08` → `#9C7418` → `#C8960C` → `#FFD700`) at 44% blended over a warm base (`-modulate 100,95,102 -sigmoidal-contrast 2x50%`, blue channel ×0.90), then `-sigmoidal-contrast 1.4x58%` for drama → `pandemonium.jpg`.
- **Re-deriving the aged-codex master** (from the clean grade, never from the original — aging layers on top): light grade + deeper darks (`-modulate 100,90,101 +level 3%,100%`), a weak veiling glow + highlight bloom (blurred `screen` passes), a plasma+grain parchment texture `overlay`-blended at ~40%, then a **re-anchor to the palette** — the Imperator tritone ramp (`#0E0C08` → `#9C7418` → `#C8960C` → `#FFD700`) applied as a `-clut` gradient-map and `blend`-composited at ~34% so the aged tones snap back to obsidian/amber/gold instead of drifting into generic sepia — an **obsidian** burnt-edge vignette (`radial-gradient:'#ffffff'-'#120c05' -level 0,100%,1.9`, `multiply`), and `+noise Gaussian` film grain → `pandemonium-aged.jpg`. Blur radii scale with resolution (~×3 from the 1400px proxy to the 4312px master). Raise the re-anchor blend toward the palette for a cleaner/more-Imperator look, lower it for more sepia parchment.
- **Resolution**: set `IMPERATOR_LOCK_SIZE=WxH` in the environment before calling `lock.sh`, or pass `--size` directly to `wallpaper.py`.

## Performance Considerations

- The lock image is recomposited by `wallpaper.py` on every single lock invocation (not cached) — decoding the ~2880px PNG, cover-scaling it, the down/upscale panel blur, and the HUD draw are fast (well under human-perceptible lock delay) but are real CPU work paid at every lock, not a one-time cost.
- The generated PNG is written to `/tmp` (typically tmpfs), avoiding disk I/O for the ephemeral lock image.
- `swaylock --scaling fill` avoids letterboxing/scaling artifacts but assumes the generated image's aspect ratio should be stretched or cropped to fill the screen exactly — mismatched `IMPERATOR_LOCK_SIZE` versus actual monitor resolution will scale rather than reflow the composition.

## Notes

- `lock.sh` hardcodes its own directory via `dirname "$(realpath "$0")"` to locate `wallpaper.py` — moving `lock.sh` without `wallpaper.py` alongside it will break the script.
- The baked panel layout (`wallpaper.py`) and the live ring/clock size (`lock.sh` `FS`/`R`/`TH`) are set independently — they must be changed together, or the real ring collides with the crest/epitaph. The `--preview-clock` render mocks the ring so you can check the layout without launching swaylock; still verify on a real lock after any resolution or layout change.
- Solid fallback color (`color=0E0C08ff` in `config`) only applies when swaylock is invoked *without* an image; irrelevant through `lock.sh`.
- Hibernation: the idle chain (`Arrakis-sunset/swayidle.service`) suspends at 40 min, not hibernates — the machine has only volatile zram swap and no `resume=`. Real hibernation needs a disk swapfile ≥ RAM plus `resume=`/`resume_offset` in limine and the initramfs `resume` hook.
- Only the deployed rice is tracked: `config`, `lock.sh`, `wallpaper.py`, and the runtime assets `assests/pandemonium.png` + `assests/shield.png`. The high-res derivation sources (`pandemonium-original.jpg`, `pandemonium-aged.jpg`, `Ziegler.png`, and any clean `pandemonium.jpg`) are `.gitignore`d — kept locally to re-derive the runtime assets, but not part of the theme itself. The re-derivation commands above assume you still have them.
