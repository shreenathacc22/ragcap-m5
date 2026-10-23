# ragcap: project status

Last updated 2026-10-23. Machine: Apple M5 Pro (24 GB, macOS 26.6). Repo: https://github.com/shreenathacc22/ragcap · Live site: https://shreenathacc22.github.io/ragcap/

The system is built, tested and documented on this machine. `./recreate.sh` ends `RECREATE OK` with every fingerprint matching, `./services.sh check` ends `CLEAN START OK`, and `scenarios.py` has no unexpected failures. Evidence for every item: `docs/SOP_ragcap_build.pdf`.

Start after a reboot: `./services.sh start && ./services.sh check`.

## Completed

| Stage | What's done (SOP section) |
|---|---|
| Pre-work (3) | Requirements, components, design decisions in the code, the rules that keep results honest (test sets frozen in git before the code) |
| Preparation (4) | uv + Python 3.12, Ollama standalone, models; no Homebrew, Docker or admin rights |
| Implementation (5) | Native Postgres 16.2 + pgvector 0.6.2 through `pgctl.sh`; schema; ingestion with version metadata; the LangGraph (router, retrieve, grade, rewrite, generate, SQL agent, general); FastAPI, web page, Gradio; P&ID branch; Docling in `.venv-docling`; `services.sh`, `recreate.sh`, `scenarios.py`; lean and recommended model profiles |
| Testing (6) | Clean start from a stopped machine; fingerprints; version filter OFF/ON (superseded 51.6% → 0.0%, controls 20/20, ≤1 ms); 18 scenarios (12 pass, 1 observed, 5 known weaknesses, 0 unexpected); 3 runs per set: router 100%, answers 92.6% tuned / 80% unseen, 96% unseen with the qwen3:8b grader; answer-level filter 88.9% → 92.6%; P&ID 38/39 tags, 4/12 answers; browser checks of both interfaces; upload; LangSmith opt-in non-fatal; backup/restore; measured model memory |
| Troubleshooting (8) | Every problem met on this machine with cause and fix (socket path limit, ports, sleep, model memory, wrong vision-model label, result-file overwrites) |
| Model choice | Installed: llama3.2:3b, nomic-embed-text (required), qwen3:8b (recommended grader), qwen2.5vl:3b (drawings), 10 GB. Tested and removed: llama3.1:8b, qwen2.5vl:7b. Details: `docs/APPLE_SILICON.md` section 7 |
| Documents | SOP (8 pages), runbook (5), recreate guide (6), install guide (4), 15-slide deck rebuilt from `docs/build_deck.js`; site page updated locally with M5 results and replay; all M5-only |

## Pending

| Item | Why not done | What's needed |
|---|---|---|
| Push the repository | Deferred to the deployment stage; `git` needs the Xcode license accepted | `sudo xcodebuild -license accept` (admin), then commit and push |
| Publish the showcase site | Deferred to the deployment stage | `./publish_site.sh` |
| Vercel deployment | Deferred; needs a Vercel login | vercel.com → sign in with GitHub → Add New → Project → import `shreenathacc22/ragcap` → Framework "Other", Output Directory `site` → Deploy (deck slide 13) |
| LangSmith tracing | Deferred; needs an API key | `.env`: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...`, `LANGSMITH_PROJECT=ragcap` |
| Switch to the recommended profile | Your choice; lean is the default | add `GRADE_MODEL=qwen3:8b`, `GRADE_MODE=escalate`, `GRADE_MAX_TOKENS=600` to `.env` |
| P&ID relational questions | A bigger grader and a bigger answering model both fail M1/M2 although the right drawing is retrieved | store each drawing's connections as structured rows the SQL agent can query |
| Multi-hop questions | D3, doc-015, h-doc-15: the grader keeps one of the two needed passages | split a two-part question and retrieve per part |
| SQL plausibility | S2, db-004: an unasked condition or grouping | re-run without the extra clause when a result looks implausible |
| Real P&ID drawings, Docling on real PDFs | No real data set yet | a drawing or PDF set with its own golden questions |
