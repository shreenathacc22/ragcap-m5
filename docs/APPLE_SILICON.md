# Running ragcap on an Apple Silicon Mac (M1–M5, Pro/Max)

Written for: running this project on an Apple Silicon Mac. Verified on an Apple M5 Pro (15 cores, 24 GB, macOS 26.6) on 2026-10-22/23: `recreate.sh` ends `RECREATE OK` with every fingerprint matching, and `services.sh check` ends `CLEAN START OK`. Time: about 15 minutes plus model downloads. Step-by-step manual install: `docs/INSTALL_AND_USE.md`.

## 1. Install the prerequisites (no admin rights, no Homebrew, no Docker needed)

This is the path that was used on the M5 Pro, where Homebrew, Docker and an admin password were not available:

```bash
# Python 3.12 (arm64) through uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12                        # gives ~/.local/bin/python3.12

# Ollama: the standalone arm64 binary, into your home folder
mkdir -p ~/.local/opt/ollama && cd ~/.local/opt/ollama
curl -fsSL -o ollama-darwin.tgz https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz
tar xzf ollama-darwin.tgz && rm ollama-darwin.tgz && ln -sf ~/.local/opt/ollama/ollama ~/.local/bin/ollama
nohup ollama serve > ~/.ollama/serve.log 2>&1 &          # or install the Ollama app, which starts it for you

ollama pull llama3.2:3b                    # the LLM all results were recorded with
ollama pull nomic-embed-text               # embeddings (768 dimensions; must not change)
```

Postgres needs no separate install: `pgctl.sh` (called by `recreate.sh`) runs Postgres 16.2 + pgvector 0.6.2 natively from the pip wheel `pgserver`, with its data in `.pgdata/`, listening on 127.0.0.1:5433 with the password in `.env`. If Docker Desktop is installed, `pgctl.sh` uses the `pgvector/pgvector:pg16` container instead (pgvector 0.8); force either with `RAGCAP_PG=local` or `RAGCAP_PG=docker`.

The Homebrew route works too: `brew install python@3.12` and `brew install --cask ollama` (plus `docker` if you want the container backend).

Check: `python3.12 --version` prints 3.12.x, `ollama list` shows both models.

## 2. Rebuild with one command

```bash
cd ragcap                                  # the repository (build/ in the project folder)
PY=$(command -v python3.12) ./recreate.sh
```

`recreate.sh` keeps the Mac awake (`caffeinate`), creates `.env` with a random database password if there is none, builds `.venv`, starts Postgres through `pgctl.sh`, ingests the 16 versioned runbooks and the broker table, runs the data checks, verifies the fingerprints, runs the version-filter ablation and three smoke questions. It ends with `RECREATE OK`, or stops with `FAIL: <reason>`. On the M5 Pro it takes about 20 seconds once the models are pulled.

A `.venv` copied from another Mac does not run: rename or delete it and let `recreate.sh` build a new one. A copied `.env` can be kept; the database is created with that password.

Recorded on the M5 Pro (2026-10-22/23):

| Check | Result |
|---|---|
| Counts | `16 docs, 16 chunks, 8 superseded, 1 tables` |
| Golden, corpus and P&ID sha1 (drawings included) | match |
| Ablation headline | OFF `99/192 (51.6%)` → ON `0/192 (0.0%)`; control 20/20 |
| Pair similarity old vs current | 0.963–0.990, old first 1/8 |
| Median retrieve, interleaved | 12–13 ms both ways, never more than 1 ms apart |
| Unseen set, 3 runs: router / answers | 100% / 80% (identical runs); 96% with the recommended grader |
| Tuned set, 3 runs: router / answers | 100% / 92.6% (identical runs) |
| Answer-level filter OFF / ON (27 cases) | 88.9% / 92.6%; multi-hop 0/2 → 1/2 |
| Time per question: document / database / general | 1.1 / 0.9 / 0.3 s |
| P&ID: tags read / answers | 38/39 / 4/12, 5–12 s per drawing |
| Scenario catalogue | 12 pass, 5 known weaknesses, 0 unexpected |

Results files: `results/m5_summary.md`, `results/qwen3esc_summary.md`, `results/m5_answer_off_*`, `results/m5_answer_on_*`, `results/pid_eval_summary.md`, `results/scenarios_*.md`.

## 3. Use it

```bash
.venv/bin/uvicorn api:app --port 8000        # browser: http://127.0.0.1:8000/  (pick another port if 8000 is taken)
.venv/bin/python ui.py                       # Gradio: http://127.0.0.1:7860
.venv/bin/python try.py "Which brokers are above 85% disk usage?"
VERSION_AWARE=0 .venv/bin/python try.py "At what disk utilisation should a broker page?"   # the trap: may say 85%
.venv/bin/python try.py "At what disk utilisation should a broker page?"                   # the fix: 75%
./pgctl.sh status                            # database: start | stop | status | psql | dump | restore | reset
./services.sh start && ./services.sh check   # everything at once, then the clean-start check (CLEAN START OK)
```

After a reboot or a sleep neither Ollama (standalone binary) nor the native Postgres starts on its own: run `./services.sh start`, then `./services.sh check` (`docs/RECREATE.md` section 2.11 has the expected output).

The scenario catalogue (`docs/RECREATE.md`, section 3) lists 18 questions with expected routes and answers.

## 4. What Apple Silicon makes possible

Run each experiment against the same frozen sets so it is comparable with the recorded results, and record it in the SOP as a new step. Done on the M5 Pro so far:

| Experiment | Result | SOP |
|---|---|---|
| Stronger grader: qwen3:8b, escalate | unseen set 80% → 96% (4 of 5 failures fixed, unanswerables still refused); tuned set unchanged at 92.6%; document questions ~3 s | step 27 |
| Bigger vision model: qwen2.5vl:7b | tags 38/39 → 39/39; P&ID answers 4/12 → 6/12; the rest fail in the 3B answering step | step 28 |
| Bigger answering model: llama3.1:8b (all nodes) | unseen 92% (one refusal worded differently), tuned 96.3% (multi-hop 2/2); P&ID 5/12, no better; 5.5 GB always resident | step 30 |

Which of these to keep is in section 7.

**Stronger grader** (run 2026-10-23: unseen set 80% → 96%; to use it every day, put the three `GRADE_` settings in `.env`):

```bash
ollama pull qwen3:8b
GRADE_MODEL=qwen3:8b GRADE_MODE=escalate GRADE_MAX_TOKENS=600 ./run_series.sh qwen3esc llama3.2:3b
.venv/bin/python summarize_series.py qwen3esc        # compare with results/m5_summary.md (same machine)
```

**Bigger answering model** (all nodes):

```bash
ollama pull llama3.1:8b
./run_series.sh llama8b llama3.1:8b && .venv/bin/python summarize_series.py llama8b
```

**Bigger vision model for the P&ID branch**:

```bash
ollama pull qwen2.5vl:7b
cp results/pid_eval_summary.md results/pid_eval_summary_m5_3b.md       # the next line overwrites it
VISION_MODEL=qwen2.5vl:7b .venv/bin/python pid_eval.py --ingest      # run 2026-10-23: 39/39 tags, 6/12 answers
```

## 5. Docling (layout-aware PDF, Word, PowerPoint parsing): verified on the M5 Pro

Keep it in its own venv; torch is large and the main `.venv` stays exactly as recorded:

```bash
uv venv --python 3.12 .venv-docling && uv pip install --python .venv-docling/bin/python docling
.venv-docling/bin/python tools/docling_convert.py some.pdf > some.md    # Markdown on stdout
.venv/bin/python -m ragcap.ingest some.pdf                             # uses .venv-docling automatically
```

Verified 2026-10-22: Docling with torch 2.14.1 (Metal backend available) converted the 7-page recreate guide in about 47 s and kept its tables as Markdown tables, which pypdf loses. `ragcap/ingest.py` tries, in order: Docling imported in `.venv`; Docling through `.venv-docling` as a subprocess; pypdf text for PDFs. `.docx`, `.pptx` and `.html` need one of the first two. The first conversion downloads Docling's layout models from Hugging Face (one time).

## 6. Things to know on this machine

- With llama3.2:3b at temperature 0, repeated runs gave identical answers; compare a new experiment with `results/m5_summary.md` from the same machine.
- The native Postgres listens on TCP only. Its Unix socket is switched off because the project path is longer than macOS's 103-byte socket limit, so always connect with `-h 127.0.0.1` (`./pgctl.sh psql` does).
- pgvector 0.6.2 (native backend) has no `hnsw.iterative_scan`; `retrieve()` falls back to `hnsw.ef_search = 1000` so the version filter still returns 6 chunks on a larger table.
- The Mac sleeps, and a sleep pauses a run. An evaluation started without `caffeinate` stood still for 16 minutes (system log: `Entering Sleep state due to 'Idle Sleep'`). The long scripts already run under `caffeinate`; for a single `eval.py`, use `caffeinate -i .venv/bin/python eval.py`.
- Never commit `.env`. The database password is fixed when the database is first created. If you lose `.env`, run `./pgctl.sh reset` (it destroys the stored data) and re-run `recreate.sh`.
- Vercel and LangSmith are machine-independent; see `STATUS.md`.

## 7. Models: what is used, and what to keep

ragcap needs two models; one more is worth having; the rest were experiments. Memory is the resident size of Ollama's runner process with that model loaded (measured with `ps -axo rss` on the M5 Pro; Ollama's own `ollama ps` under-reports the vision models).

| Role in ragcap | Model | Disk | Memory loaded | Keep? |
|---|---|---|---|---|
| router, grader, answers, SQL, general | `llama3.2:3b` | 2.0 GB | 2.4 GB | **yes, required** (every recorded result uses it) |
| embeddings, 768 dimensions | `nomic-embed-text` | 0.3 GB | 0.3 GB | **yes, required** (changing it means re-ingesting everything) |
| second-opinion grader (`GRADE_MODE=escalate`) | `qwen3:8b` | 5.2 GB | 5.5 GB | **recommended**: unseen questions 80% → 96%; loads only when the 3B grader keeps nothing |
| drawing descriptions at ingest (P&ID) | `qwen2.5vl:3b` | 3.2 GB | 5.0 GB | only if you ingest drawings; used while ingesting, never while answering |
| bigger drawing model | `qwen2.5vl:7b` | 6.0 GB | 7.7 GB | no: +1 tag and +2 answers on 12 questions for +2.7 GB |
| bigger answering model | `llama3.1:8b` | 4.9 GB | 5.2 GB | no: always resident, and 92% unseen against 96% for the escalate grader |

Three profiles:

| Profile | Models | Disk | Memory | Unseen / tuned answers |
|---|---|---|---|---|
| Lean | `llama3.2:3b` + `nomic-embed-text` | 2.3 GB | ~2.7 GB | 80% / 92.6% |
| **Recommended** | Lean + `qwen3:8b` as escalate grader | 7.5 GB | ~2.7 GB usually, ~8.2 GB peak | **96% / 92.6%** |
| With drawings | Recommended + `qwen2.5vl:3b` | 10.7 GB | +5.0 GB only while ingesting drawings | P&ID: 38/39 tags, 4/12 answers |

Why the recommended profile stays light: Ollama loads a model on first use and unloads it after 5 minutes idle, so `qwen3:8b` is resident only for a few minutes after a hard question, and the vision model only during an ingest. On 24 GB of RAM about 16 GB stays free even at the peak, which leaves room for other projects' models.

```bash
# use the recommended profile: add to .env (delete the three lines to go back to lean)
GRADE_MODEL=qwen3:8b
GRADE_MODE=escalate
GRADE_MAX_TOKENS=600

# remove the experiment models ragcap does not need (frees ~11 GB; `ollama pull` restores them)
ollama rm llama3.1:8b qwen2.5vl:7b

# watch and free memory
./services.sh status            # the "in memory" list
ollama ps                       # same, from Ollama
ollama stop qwen3:8b            # unload one model now instead of waiting 5 minutes
```

The remaining P&ID failures are not a model-size problem (SOP step 30): they need the drawing's connections stored as structured data. Do not pull bigger models for them.
