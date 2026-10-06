---
name: hyperframes-creative
description: Creative direction (brand, palette, typography, narration, beat planning) for HyperFrames demo/promo videos of the ABC IT PMO Kanban board, kept under promo/. Applies the board's corporate-blue tokens and fictitious-bank brand rules. Not for in-app UI; use design-taste-frontend-v1 for that. For motion, use hyperframes-animation.
---

# PROJECT OVERRIDES: ABC IT PMO Kanban (read first; these win over everything below)

**Scope:** video compositions in `promo/` that show off the Kanban board, such as a README demo clip or a
training walkthrough. Never edit `index.html` from this skill. Requires `hyperframes-core` /
`hyperframes-cli`, which are not installed; ask the user before installing them (command in `hyperframes-animation`).

## Brand truth (use as the design spec; do not pick a preset palette or visual style)
If `promo/design.md` does not exist, create it from these values, taken from the `:root` tokens in `index.html`:
* Wordmark: the text "ABC IT PMO" only, as a fictitious bank. **No real bank logos, names, trademarks,
  colours-as-imitation or system styling**, and no "inspired by <real bank>".
* Colours: background `#f1f6fd` (`--blue-50`) or `#ffffff`. Header/title band `#0b2545` (`--blue-900`).
  Primary accent `#1f5fae` (`--blue-600`). Text `#1d2330` (`--grey-900`), muted `#4a5263`.
  Semantic: critical `#c62828`, high `#c77700`, success `#1e7b45`. Focus/highlight `#f5b700`.
  No purple, neon or gradient text.
* Type: the system stack `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`, plus `ui-monospace`
  for IDs (`ABC-ITPM-0001`), dates and counts. Keep this even in video, so footage matches the app.
* Shape: 8px radius cards, 4px tags, and soft blue-tinted shadows (`rgba(11,37,69,0.14)`).
* Tone: calm, precise, corporate IT governance. Concrete verbs, no hype ("Elevate", "Seamless" and
  "Next-gen" are banned).

## Story spine that fits the product
1. Problem: status updates scattered across email and spreadsheets.
2. The board: four columns (Backlog, In Progress, Blocked, Done), with the summary bar showing totals and Overdue.
3. Action: add a task through the dialog (ID `ABC-ITPM-####` appears), then drag a card to Blocked.
4. Signal: filter by project or assignee, and the overdue count updates.
5. Close: "Single HTML file. Opens offline. No sign-up." plus the wordmark. Do not claim real-bank usage,
   compliance certification or data persistence. The board resets on refresh by design.

Use real seed content (for example "Patch CVE on branch teller VDI" or "UAT sign-off for mobile onboarding 4.2")
rather than lorem ipsum. Prefer screen captures or faithful HTML re-creations of the actual board UI.

## Not applicable here
Audio-reactive visuals, music, voice-over and captions are opt-in only, so propose them first. Ignore
`frame-presets/` and `palettes/*.md` unless the user explicitly asks for an alternative look.

---

**Plugin installs:** Before setup or freshness commands, follow [plugin execution rules](../hyperframes/references/plugin-installation.md) when this skill is inside a HyperFrames plugin. Standalone installs keep the update instructions below.

# HyperFrames Creative

Brand, pacing, style, narration, and composition direction. Use after the technical contract from `hyperframes-core` is in place.

For motion patterns, scene blueprints, transitions, and CSS marker effects, use `hyperframes-animation` — this skill is intentionally non-animation.

> **Read these two FIRST for any non-trivial composition — they override web instincts:**
>
> - `references/house-style.md` — "interpret the prompt, generate real content," the lazy-default list, and the background/foreground layer recipe. This is what turns a literal restyle into a _concept_.
> - `references/video-composition.md` — video-medium scale, depth, and foreground detail. It explains how to avoid empty web-page layouts without imposing a universal element count.
>
> Skipping these is the single biggest cause of generic, web-page-looking output. They are not optional rows in the routing table below — for anything beyond a one-line edit, open both before you choose colors or write HTML.

## Workflow

1. If a project has a design spec, **read it first** and treat its frontmatter tokens as brand truth (colors, fonts, spacing, tone, constraints). Which file to read (precedence `frame.md` → `design.md` → `DESIGN.md`) and how to parse it (frontmatter = normative, prose = context) are defined once in [`references/design-spec.md`](references/design-spec.md) — resolve and load per that doc.
2. If no design spec exists and the user asks for visual direction, choose a route:
   - Ready-made frame-preset (optional) → `frame-presets/` (adopt a `FRAME.md` as `frame.md`; see `references/design-spec.md`)
   - Named style or mood → `references/visual-styles.md`
   - Fast defaults → `references/house-style.md`
   - Interactive selection → `references/design-picker.md`
3. For multi-scene work, plan beats and rhythm before writing HTML → `references/beat-direction.md`. For scene transitions, jump to `hyperframes-animation/transitions/`.
4. For motion-heavy work, read `references/motion-principles.md` (high-level guardrails), then go to `hyperframes-animation` for atomic rules.

## Routing

| Topic                                                                                                   | Read                                           |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Adopt a ready-made frame-preset as `frame.md` (optional)                                                | `frame-presets/` · `references/design-spec.md` |
| Default palettes, motion, typography, lazy defaults to question                                         | `references/house-style.md`                    |
| Named style presets, mood-to-style routing                                                              | `references/visual-styles.md`                  |
| Palette-specific color tokens                                                                           | `palettes/*.md`                                |
| Composition patterns — PiP, text-behind-subject, title card, slide show                                 | `references/composition-patterns.md`           |
| Stats / infographic presentation                                                                        | `references/data-in-motion.md`                 |
| Structured expansion for open-ended prompts                                                             | `references/prompt-expansion.md`               |
| Video-medium density, scale, color, frame composition                                                   | `references/video-composition.md`              |
| Per-beat direction, rhythm planning, transition timing                                                  | `references/beat-direction.md`                 |
| Post-authoring spec verification (colors, type, corners, spacing, depth)                                | `references/design-adherence.md`               |
| High-level motion guardrails and GSAP-quality rules                                                     | `references/motion-principles.md`              |
| Font selection, pairings, rendered-video type guardrails                                                | `references/typography.md`                     |
| Story doctrine — hook language, value-before-evidence, storyboard-as-proposal, source-traceable visuals | `references/story-spine.md`                    |
| Script pacing, tone, openings, number pronunciation                                                     | `references/narration.md`                      |
| Precomputed audio bands mapped to motion                                                                | `references/audio-reactive.md`                 |

## Scripts

- `scripts/contrast-report.mjs` — inspect contrast warnings from rendered frames.
- `scripts/extract-audio-data.py` — pre-extract audio bands for audio-reactive compositions.
- `scripts/package-loader.mjs` — support script for bundled creative tooling.

`contrast-report.mjs` resolves helper packages from the current project first, then can bootstrap the bundled HyperFrames package version. Set `HYPERFRAMES_SKILL_PKG_VERSION=<version>` only when running the skill outside the bundled CLI/skill install and you need to pin that bootstrap version explicitly.

Run with explicit paths, for example:

```bash
python <SKILL_DIR>/scripts/extract-audio-data.py <audio-file>
```

Animation analysis (`animation-map.mjs`) lives in `hyperframes-animation/scripts/`.

## Boundaries

- Do not override `hyperframes-core` technical rules.
- Do not require a design system for a minimal technical composition.
- Do not add extra scenes, narration, music, captions, or transitions unless the request calls for them or you first propose the expansion.
- Keep recipe references task-specific; do not read every reference for simple edits.
