# Connectors (ABC IT PMO Kanban)

Adapted from `data/CONNECTORS.md` in anthropics/knowledge-work-plugins. Upstream skills use `~~category`
placeholders (for example `~~data warehouse`) for whatever MCP tool the user has connected. This project
connects none of them.

| Upstream placeholder | Upstream servers | In this project |
|---|---|---|
| `~~data warehouse` | Snowflake, Databricks, BigQuery, Definite | **None.** The data is `state.tasks` in `index.html` (seed tasks plus anything added in the session). |
| `~~notebook` | Hex, Jupyter | **None.** Don't produce notebooks. |
| `~~product analytics` | Amplitude, Mixpanel | **None.** |
| `~~project tracker` | Atlassian (Jira/Confluence), Linear, Asana | **None.** The Kanban board *is* the tracker. |

## Rules
* Never add a fetch, MCP call or import to pull dashboard data. The only allowed network call in
  `index.html` is FormSubmit's AJAX endpoint (see CLAUDE.md).
* If the user pastes or attaches data (for example a Jira CSV export), parse it once and embed it as a JS
  constant in a standalone `dashboards/<name>.html`. Map its columns onto the task fields
  (`id, title, project, category, assignee, priority, status, due`) and label the file as a snapshot.
* If a step in the skill says "query the warehouse", skip it and use the board data instead.
