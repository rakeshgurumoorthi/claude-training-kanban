#!/bin/sh
# SessionStart hook: reminds you in Claude Code about the IT Project Briefing.
# The website shows its own popup (see BRIEFING_STARTS_AT in index.html and
# v2/index.html); this hook only runs in Claude Code, never in a browser.
# Prints nothing once the briefing has started.

BRIEFING_STARTS_AT=202610071400 # YYYYMMDDhhmm, local time

[ "$(date +%Y%m%d%H%M)" -ge "$BRIEFING_STARTS_AT" ] && exit 0

printf '%s\n' '{"systemMessage": "Reminder: IT Project Briefing, Wednesday 7 October 2026 at 2:00 PM, Town Hall Meeting Room."}'
