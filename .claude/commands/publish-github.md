---
description: Security-scan, then push to GitHub, refresh the README screenshot and README, CI/CD workflow, GitHub Pages and the repo About section
argument-hint: <github-repo-url>
allowed-tools: Bash(git:*), Bash(gh:*), Bash(grep:*), Bash(node:*), Bash(curl:*), Bash(gitleaks:*), Bash(python3:*), Bash(pkill:*), Bash(rm -rf .playwright-mcp), Read, Edit, Write, mcp__playwright__browser_resize, mcp__playwright__browser_navigate, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_close
---

Publish this project to GitHub. The target repository is: **$ARGUMENTS**

If `$ARGUMENTS` is empty or is not a GitHub repo URL (`https://github.com/<owner>/<repo>[.git]` or `git@github.com:<owner>/<repo>.git`), stop and ask the user for the repo link. Parse `<owner>/<repo>` from it and use it in every step below.

Work through the steps in order. The security scan runs **first** because it gates the push: nothing may reach GitHub until it passes. Keep a short checklist as you go and report it at the end.

## 0. Preflight

1. `gh auth status`: if not logged in, stop and tell the user to run `gh auth login`.
2. `gh repo view <owner>/<repo> --json name,visibility,defaultBranchRef,homepageUrl,description`:
   - If the repo does not exist, ask the user whether to create it (`gh repo create <owner>/<repo> --public --source=. --remote=origin`). Do not create it without a yes.
   - If it is private, warn that GitHub Pages on a private repo needs a paid plan.
3. `git remote -v`: if there is no `origin`, add it. If `origin` points to a different URL, show both and ask before changing it.
4. `git status`: note uncommitted changes. They will be included in the commit in step 5 only after the security scan passes.

## 1. Security scan (blocking gate)

Scan every file that would be pushed (`git ls-files` plus untracked, non-ignored files from `git ls-files --others --exclude-standard`) **and** the existing commit history (`git log -p --all`).

1. If `gitleaks` is installed, run `gitleaks detect --source . --redact -v` (history) and `gitleaks detect --source . --no-git --redact -v` (working tree).
2. Always also run a grep pass, ignoring `.git/`, for:
   - Private keys: `-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----`
   - Cloud and API tokens: `AKIA[0-9A-Z]{16}`, `ghp_[A-Za-z0-9]{36}`, `github_pat_`, `gho_`, `xox[baprs]-`, `sk-[A-Za-z0-9]{20,}`, `sk-ant-`, `AIza[0-9A-Za-z_-]{35}`
   - Generic secrets: `(password|passwd|secret|api[_-]?key|token|client[_-]?secret)\s*[:=]\s*['"][^'"]{6,}`
   - Real email addresses: any address that is not the `YOUR_EMAIL@example.com` placeholder or `noreply` addresses. In this project, `FORMSUBMIT_ENDPOINT` in `index.html` **must** still contain the placeholder when pushed. A real address there is a finding.
   - Sensitive files: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`, `*.sqlite`, `credentials*`, `.DS_Store`, `.vscode/` or `.claude/settings.local.json`
3. Run the project constraint check from CLAUDE.md. It should print nothing:
   `grep -nE "localStorage|sessionStorage|indexedDB|document\.cookie|alert\(|confirm\(|!important|<link|src=\"http" index.html`
4. Make sure a `.gitignore` exists that covers at least `.DS_Store`, `.env*`, `*.pem`, `*.key`, `.claude/settings.local.json`, `node_modules/` and `.playwright-mcp/`. Create or extend it if needed.

**If anything is found:** stop. List each finding with `file:line` and the secret redacted. Do not push. Offer fixes: replace with a placeholder, remove the file from tracking with `git rm --cached`, or add it to `.gitignore`. If a secret is already in **history**, tell the user to rotate it, and that removing it needs a history rewrite (`git filter-repo`) plus a force push. Never do either without explicit approval. Continue only after the user confirms the findings are resolved or are false positives.

## 2. Screenshot (Playwright MCP)

Capture a fresh screenshot of the local `index.html` so the README always shows the current UI. Use the Playwright MCP tools (server `playwright` in `.mcp.json`). Its browser blocks `file://` URLs, so serve the folder locally for the capture:

1. Start a local server in the background, bound to localhost only: `python3 -m http.server 8765 --bind 127.0.0.1`
2. `browser_resize` to 1440 × 900, then `browser_navigate` to `http://127.0.0.1:8765/index.html`.
3. `browser_take_screenshot` with `filename: "docs/screenshot.png"` and `scale: "css"` (viewport only, not full page).
4. Read the PNG back and check that it shows the header, the summary strip, the filter bar and all four columns with seed cards. If the page is blank or broken, report that and don't add the image.
5. Clean up: `browser_close`, stop the server (`pkill -f "http.server 8765"`) and delete Playwright's log folder (`rm -rf .playwright-mcp`).

If the Playwright MCP server isn't available, skip this step, keep any existing `docs/screenshot.png`, and say so in the report. Nothing in the screenshot may show a real email address or personal data; the seed data is fictitious.

## 3. README.md (create or update)

Read `CLAUDE.md` and `index.html` to understand the app, then create or refresh `README.md`. Keep any user-written sections that are still accurate. Include:

- Title and a one-line description (a demo IT PMO Kanban board for a fictitious bank, "ABC IT PMO")
- **Live demo** link: `https://<owner>.github.io/<repo>/` (lowercase the owner)
- The screenshot right under the live demo link: `![ABC IT PMO Kanban board with Backlog, In Progress, Blocked and Done columns](docs/screenshot.png)`
- Features (columns, drag-and-drop, filters, summary, Add Task dialog, FormSubmit email notification)
- How to run: open `index.html` directly, no build or server
- Configuration: set the email in `FORMSUBMIT_ENDPOINT`, plus FormSubmit's one-time activation. Use only the placeholder in the README.
- Constraints: vanilla, single file, no persistence, no external resources
- CI/CD: what the workflow checks and that `main` deploys to Pages
- A note that this is a fictitious demo, with no real bank branding

No real email addresses, tokens or personal data.

## 4. GitHub Actions CI/CD

Create or update `.github/workflows/pages.yml`. Edit the existing file rather than adding a second Pages workflow. It must have:

- Triggers: `push` to `main`, `pull_request` to `main`, `workflow_dispatch`
- **`ci` job** (runs on every trigger):
  - checkout
  - The constraint grep from CLAUDE.md. Fail the job if it prints anything.
  - Extract the `<script>` block from `index.html` to a temp file and run `node --check` on it (`actions/setup-node@v4`)
  - A secret-scan step (`gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`, or the same grep patterns as step 1)
  - Fail if `FORMSUBMIT_ENDPOINT` does not contain `YOUR_EMAIL@example.com`
- **`deploy` job**: `needs: ci`, runs only on push to `main` or `workflow_dispatch` (`if: github.event_name != 'pull_request'`), with the `github-pages` environment, `configure-pages@v5`, a staged `_site/` holding only `index.html`, `upload-pages-artifact@v3` and `deploy-pages@v4`
- Least-privilege permissions: `contents: read` at the top level, and `pages: write` plus `id-token: write` only on `deploy`
- A `concurrency` group for Pages

Check that the YAML is valid before committing (e.g. `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" .github/workflows/pages.yml` if PyYAML is available).

## 5. Commit and push

1. Re-run the step 1 grep pass on the final staged diff (`git diff --cached`) as a last check.
2. Stage only the intended files, by name, including `docs/screenshot.png` if step 2 produced it. Never use `git add -A` blindly; show `git status` first.
3. Commit with a clear message ending with the attribution line from the session's instructions.
4. `git push -u origin <current-branch>`. **Never force-push.** If the push is rejected because the remote has commits you don't have, stop and ask: offer `git pull --rebase`, but don't run it unasked.

## 6. GitHub Pages (create or update)

Configure Pages to build from GitHub Actions:

- Check: `gh api repos/<owner>/<repo>/pages` (a 404 means Pages is not enabled)
- Not enabled: `gh api -X POST repos/<owner>/<repo>/pages -f build_type=workflow`
- Enabled with a different source: `gh api -X PUT repos/<owner>/<repo>/pages -f build_type=workflow`
- Read back `html_url`. That is the Pages URL used below.

Then watch the workflow run started by the push: `gh run list --workflow pages.yml --limit 1`, then `gh run watch <id> --exit-status`. If it fails, show the failing step's log (`gh run view <id> --log-failed`), fix the cause, and push again (repeat step 5). Once it succeeds, run `curl -sSfI <pages-url>` to confirm the site responds with 200. The first deploy can take a minute.

## 7. Repo About section

Update the description, website and topics in one call:

```
gh repo edit <owner>/<repo> \
  --description "Demo IT PMO Kanban board for a fictitious bank — single-file vanilla HTML/CSS/JS, deployed with GitHub Pages" \
  --homepage "<pages-url>" \
  --add-topic kanban --add-topic project-management --add-topic vanilla-js \
  --add-topic html-css-javascript --add-topic github-pages --add-topic demo
```

If a description already exists and differs, keep its intent and refine it rather than overwriting it wholesale. Confirm with `gh repo view <owner>/<repo> --json description,homepageUrl,repositoryTopics`.

## 8. Report

Finish with a short summary:

- Security scan: pass, or the findings and how they were resolved
- Commit SHA pushed and the branch
- Screenshot: captured to `docs/screenshot.png`, or skipped and why
- README: created or updated
- Workflow: created or updated, and the result of the latest run, with its link
- Pages URL, and whether it returned 200
- About section: description, website and topics set

Report anything skipped or failed plainly, with the relevant output.
