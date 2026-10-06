# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A demo/training IT PMO Kanban board for a fictitious bank ("ABC IT PMO"). Each version of the app is one file holding the markup, one `<style>` block and one `<script>` block. `index.html` is v1, served at the Pages root, and is kept as-is. `v2/index.html` is the redesign, served at `/v2/`, with a Board/Portfolio view switch, priority filter chips and a dashboard. The two files do not share code, so a fix to shared behaviour (validation, FormSubmit, drag and drop) has to be made in both. The architecture notes below apply to both; v2 adds `state.view`, `state.sort`, `state.animateId` and `state.animateBars`, plus `renderDashboard()`, which `renderBoard()` calls. Do not use any real bank's logo, trademarks or system styling. The brand is a text wordmark plus a corporate blue palette.

## Hard constraints (keep these when editing)

- Vanilla HTML/CSS/JS only: no frameworks, libraries, build step, bundler or npm.
- Single file that runs by double-clicking it (`file://`), with no server.
- No external resources: no CDN, web fonts or image files. Use the system font stack and inline SVG or Unicode for icons.
- No persistence: no localStorage, sessionStorage, IndexedDB or cookies. A refresh resets the board to the seed data on purpose, and the header note says so.
- The only network call is FormSubmit's AJAX endpoint. Never send data anywhere else.
- The WhatsApp chat widget's `wa.me` links are not network calls: they open WhatsApp in a new tab only when the user clicks one. Keep their pre-filled text to the fixed `CHAT_SUGGESTIONS`, never board data.
- No `alert()`, `confirm()` or `!important`. Errors appear inline and notices as toasts.

## Commands

There is no build or test suite.

- Run: `open index.html` (v1) or `open v2/index.html` (v2)
- Syntax-check the script: extract the `<script>` block to a scratch file and run `node --check` on it.
- Constraint check (should print nothing):
  `grep -nE "localStorage|sessionStorage|indexedDB|document\.cookie|alert\(|confirm\(|!important|<link|src=\"http" index.html v2/index.html`

## Project skills

`.claude/skills/` holds third-party skills (tracked in `skills-lock.json`) customized for this board: `design-taste-frontend-v1` (UI polish), `build-dashboard` (PMO dashboard with inline SVG/CSS charts), `hyperframes-animation` (CSS/WAAPI motion in the app; HyperFrames videos in `promo/`) and `hyperframes-creative` (promo video brand). Each starts with a **PROJECT OVERRIDES** section that wins over the upstream text below it. `npx skills update` overwrites these files, so re-apply the overrides after updating.

## Architecture (inside the `<script>`)

- **Config at the top:** `FORMSUBMIT_ENDPOINT` is the one place the email address goes. While it still contains the `YOUR_EMAIL@example.com` placeholder, `handleSubmit` skips the fetch and shows the warning toast. FormSubmit needs one-time activation: the first submission sends a confirmation email, and nothing is delivered until its link is clicked.
- **Single state object:** `state = { tasks, filters, nextId, pendingDeleteId, openMoveId, focusAfterRender }`. UI-only flags (which card has its Move menu or delete confirm open, and what to focus next) also live in `state`.
- **Render from state:** `renderBoard()` rebuilds every column's card list from `getFilteredTasks()`, using `renderCard()` HTML strings, then updates the count badges, filter result text and `renderSummary()`. The summary always counts all tasks, not just filtered ones. Never change card contents directly; change `state` and call `renderBoard()`. Focus survives a re-render through `state.focusAfterRender`, a CSS selector.
- **Mutations:** `addTask`, `moveTask`, `deleteTask` and `applyFilters` change `state`, then re-render.
- **Escaping:** every interpolated value in an HTML string goes through `escapeHtml()`.
- **Event delegation:** drag-and-drop (`wireDragAndDrop`) and card buttons (`wireCardActions`, routed by `data-action`) are attached once to `#board`, not per card, because cards are recreated on every render.
- **Columns:** `buildColumns()` builds the column shells once from `STATUSES`. Element ids derive from `slug(status)`, e.g. `col-in-progress-list`.
- **Add Task form:** a native `<dialog>`. `validateForm()` writes errors into `<p id="{fieldId}Err">` elements and sets `aria-invalid`. Submit is optimistic: the card is added first, then `notifyNewTask()` runs inside try/catch, and a failure only shows a warning toast.
- **Task IDs:** `ABC-ITPM-####`, from `formatId(state.nextId++)`.
- **WhatsApp chat widget:** `WHATSAPP_NUMBER` and `CHAT_SUGGESTIONS` sit with the config. `useChatSuggestions()` is a custom hook called from `init()`. It fills `#chatQueries` with `wa.me` links, opens `#chatDialog` when `#chatLauncher` (fixed bottom right) is clicked, and returns `{ open, close }`. Toasts sit above the launcher, and `showBriefing()` waits for the chat dialog to close.
- **Dates:** compared as local `YYYY-MM-DD` strings (`todayISO()`, not UTC). Seed due dates are offsets from today, so some seed cards always show as overdue.
