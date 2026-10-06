# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A demo/training IT PMO Kanban board for a fictitious bank ("ABC IT PMO"). The whole app is one file, `index.html`, holding the markup, one `<style>` block and one `<script>` block. Do not use any real bank's logo, trademarks or system styling. The brand is a text wordmark plus a corporate blue palette.

## Hard constraints (keep these when editing)

- Vanilla HTML/CSS/JS only: no frameworks, libraries, build step, bundler or npm.
- Single file that runs by double-clicking it (`file://`), with no server.
- No external resources: no CDN, web fonts or image files. Use the system font stack and inline SVG or Unicode for icons.
- No persistence: no localStorage, sessionStorage, IndexedDB or cookies. A refresh resets the board to the seed data on purpose, and the header note says so.
- The only network call is FormSubmit's AJAX endpoint. Never send data anywhere else.
- No `alert()`, `confirm()` or `!important`. Errors appear inline and notices as toasts.

## Commands

There is no build or test suite.

- Run: `open index.html`
- Syntax-check the script: extract the `<script>` block to a scratch file and run `node --check` on it.
- Constraint check (should print nothing):
  `grep -nE "localStorage|sessionStorage|indexedDB|document\.cookie|alert\(|confirm\(|!important|<link|src=\"http" index.html`

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
- **Dates:** compared as local `YYYY-MM-DD` strings (`todayISO()`, not UTC). Seed due dates are offsets from today, so some seed cards always show as overdue.
