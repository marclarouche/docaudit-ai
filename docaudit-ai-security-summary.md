# DocAudit AI Security Summary

Date: 2026-10-18. Scope: app.py, src/docaudit, tests, config, git history, installed dependencies (92 packages in project .venv, Python 3.15). Checklist source: security-tests.md.

## Tools run

| Tool | Version | Scope / config |
|---|---|---|
| Bandit | 1.9.4 | app.py, src (589 LOC) |
| Semgrep | 1.180.0 | rulesets p/python, p/security-audit, p/secrets (236 rules, 13 tracked files, metrics off) |
| pip-audit | 2.10.1 | pip freeze of project .venv, 92 packages (--no-deps) |
| Safety | 3.8.1 | same freeze (deprecated `check` command, free DB) |
| gitleaks | 8.30.1 | `git` mode (1 commit) and `dir` mode (working tree, redacted) |
| TruffleHog / git-secrets | not installed | gitleaks used as substitute |
| Dependabot / Snyk | not run | GitHub/SaaS integrations; owner action (see below) |

Bandit, pip-audit and Safety were installed with `pip --target` into a scratch directory outside the project. Nothing was added to the project's .venv or pyproject.toml.

## Findings

| # | Severity | Location | Tool | Status |
|---|---|---|---|---|
| 1 | Low (no fix available, not reachable) | nltk 3.10.3 (transitive via textstat), PYSEC-2026-3740 / GHSA-8mgp-746c-j5xp / CVE-2026-81726 | pip-audit, Safety | Accepted risk, upstream unpatched |
| 2 | Info (false positive) | .venv/share/jupyter/nbextensions/pydeck/index.js.map line 6 (2 hits, generic-api-key) | gitleaks dir | False positive, third-party source map in ignored .venv |
| - | none | Bandit: 0 issues. Semgrep: 0 findings. gitleaks git history: no leaks. gitleaks on app.py, src: no leaks | | Clean |

## What was fixed

Nothing. No real findings in project code, so no source or dependency changes were made. Files written: this report only.

## False positives and accepted risks

1. nltk PYSEC-2026-3740: File sandbox (pathsec) bypass in model save/load helpers (TransitionParser, AveragedPerceptron, PerceptronTagger.save_to_json, save_maxent_params). It requires an app that enables nltk pathsec and lets untrusted users choose model paths. DocAudit imports nltk only through textstat, never calls those APIs, and never passes user-supplied paths to nltk. The advisory lists no patched version, so there is nothing to upgrade to. Not exploitable here.
2. gitleaks pydeck source map: vendored third-party JS in .venv (gitignored, not committed, not part of the project).

## Streamlit-specific checks (manual review)

| Check | Result |
|---|---|
| `unsafe_allow_html` / `st.markdown` / `st.write` with user text | None used. Untrusted headings and text are rendered with `st.text` and `st.dataframe` (comment in app.py documents this). Pass. |
| pickle / `st.cache_data` / `st.cache_resource` | No pickle and no cache decorators. `st.session_state` holds only pydantic models created from the server's own parse of the current upload. Pass. |
| Unsafe deserialization / eval / exec / subprocess / os.system | None. YAML is loaded with `yaml.safe_load`, 64 KB cap, and a test confirms `!!python/object` payloads are rejected. Pass. |
| Upload handling | Extension allowlist (txt, md, docx), 10 MB cap (also `maxUploadSize = 10`), UTF-8 and control-character checks, DOCX zip-bomb limits (entry count, expanded size), duplicate/traversal/encrypted entries rejected, DOCTYPE/ENTITY (XXE) rejected, VBA/embeddings/ActiveX/macros rejected, nesting depth limit. Files are never extracted to disk. Pass. |
| Error handling / logging | Uploaded content never logged; generic error shown to user. Pass. |
| Secrets | No secrets, no `st.secrets` use required; no credentials in code or history. Pass. |
| Network exposure | .streamlit/config.toml binds to 127.0.0.1, usage stats off. Pass for local use. |
| Authentication | None. By design a single-user local tool with no persistence. See owner actions. |

## Remaining items for the owner

1. If the app is ever deployed beyond localhost, put it behind an identity-aware proxy (OAuth2-Proxy, Keycloak, Authentik) or use streamlit-authenticator. The app has no auth or RBAC.
2. Watch nltk for a patched release (GHSA-8mgp-746c-j5xp) and re-run pip-audit afterward. Optionally pin nltk after the fix lands.
3. Enable Dependabot (and optionally Snyk) on the GitHub repo once pushed. Not testable locally.
4. Dependencies in pyproject.toml are mostly ranges, not hashed or locked. Consider a lock file for reproducible audits.
5. The gitleaks git scan covered only 1 commit. Rerun after the uncommitted changes (including config/grc_ai_governance.yaml) are committed. A working-tree scan of them found nothing.

## Test results

`pytest -q` in project .venv: 73 passed in 4.5 s, before and after (no code changes). The working tree's existing uncommitted changes (README.md, app.py, src/docaudit/profiles.py, tests/test_milestone2.py, config/grc_ai_governance.yaml, security-tests.md) were left untouched. No commits or pushes were made.
