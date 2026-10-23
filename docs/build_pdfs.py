from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle, PageBreak
from xml.sax.saxutils import escape
import re

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=18, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)
SM = ParagraphStyle("SM", parent=B, fontSize=8.5, leading=11)
CODE = ParagraphStyle("CODE", fontName="Courier", fontSize=7, leading=8.8, backColor=colors.HexColor("#f3f3f3"),
                      borderPadding=4, spaceBefore=3, spaceAfter=6, leftIndent=4)


def P(t, st=B): return Paragraph(t, st)
def C(t): return Preformatted(t.strip("\n"), CODE)
def T(rows, widths):
    data = [[Paragraph(escape(str(c)), SM) for c in r] for r in rows]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dde6f0")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def build(name, title, story):
    def foot(c, d):
        c.setFont("Helvetica", 7.5); c.drawString(0.7 * inch, 0.45 * inch, f"{title}  |  ragcap  |  updated 2026-10-23")
        c.drawRightString(7.8 * inch, 0.45 * inch, f"page {d.page}")
    SimpleDocTemplate(OUT + name, pagesize=letter, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                      topMargin=0.7 * inch, bottomMargin=0.8 * inch, title=title).build(story, onFirstPage=foot, onLaterPages=foot)

BASE = "ragcap"   # the clone of github.com/shreenathacc22/ragcap

# ------------------------------------------------------------------ SOP
sop = [
 P("SOP: Building, testing and running ragcap on an Apple M5 Pro", H1),
 P("Written for: an engineer who builds, tests and operates ragcap on one Apple Silicon Mac. It follows the work in order: pre-work, preparation, implementation, testing, troubleshooting. Every command was run, and every number was measured, on the machine in section 2 between 2026-10-22 and 2026-10-23. ragcap reproduces the design in Kumar's RAG Capstone PDF (LangGraph router, document RAG with grade and rewrite, SQL agent, general agent, Postgres + pgvector, FastAPI, a UI) on local models, and adds what that design did not measure: frozen test sets, repeated runs, and a version-aware retrieval filter with an OFF/ON proof."),
 P("1. Result in one table", H2),
 T([["Measure (llama3.2:3b, lean profile unless stated)", "Result on the M5 Pro", "Section"],
    ["Rebuild from zero, all fingerprints", "RECREATE OK in about 20 s", "6.2"],
    ["Clean start from a stopped machine", "CLEAN START OK", "6.1"],
    ["Router accuracy, tuned set (27) / unseen set (25)", "100% / 100%", "6.5"],
    ["Answers correct, tuned / unseen", "92.6% / 80.0% (identical over 3 runs each)", "6.5"],
    ["Answers correct, unseen, recommended profile (+ qwen3:8b second-opinion grader)", "96.0%", "6.5"],
    ["Superseded document versions retrieved, filter OFF / ON", "99/192 (51.6%) / 0/192 (0.0%); control cases 20/20 both", "6.3"],
    ["Scenario catalogue (18 questions + 1 browser test)", "12 pass, 1 observed, 5 documented weaknesses, 0 unexpected", "6.4"],
    ["P&ID drawings: tags read, answers", "38/39 tags, 4/12 answers", "6.7"],
    ["Time per question: document / database / general", "1.1 s / 0.9 s / 0.3 s", "6.5"],
    ["Memory while answering (lean / recommended peak)", "~2.7 GB / ~8.2 GB of 24 GB", "6.10"]], [3.4, 2.6, 1.0]),
 P("2. Environment", H2),
 T([["Item", "Value"],
    ["Machine", "Apple M5 Pro, 15 cores, 24 GB memory, macOS 26.6; no Homebrew, no Docker, no admin password"],
    ["Project folder", "kumar_rag-project/build (the git repository ragcap); documents in build/docs, mirrored to kumar_rag-project/docs"],
    ["Python", "3.12.15 (arm64) from uv; project venv .venv: langgraph 1.2.16, openai 3.37.0, psycopg 3.3.6, pgvector 0.5.1, fastapi, gradio, pandas"],
    ["Database", "PostgreSQL 16.2 + pgvector 0.6.2 from the pip wheel pgserver 0.1.4, run natively by pgctl.sh; data in .pgdata/; 127.0.0.1:5433, TCP only"],
    ["Models (Ollama 0.40.9, standalone binary in ~/.local/opt/ollama)", "llama3.2:3b (all LLM steps), nomic-embed-text (768-dimension embeddings), qwen3:8b (optional second-opinion grader), qwen2.5vl:3b (P&ID drawings)"],
    ["Ports", "11434 Ollama, 5433 Postgres, 8000 (or 8765) web page and API, 7860 Gradio; all bound to localhost"],
    ["Secrets", ".env (mode 600, gitignored): database password; optional LangSmith key"]], [1.8, 5.2]),
 P("3. Pre-work: decide and check before starting", H2),
 P("3.1 Requirements", B),
 T([["Requirement", "Why", "Check"],
    ["Apple Silicon Mac, 24 GB memory recommended (16 GB works with the lean profile)", "models run on the Metal GPU; the recommended profile peaks at ~8.2 GB", "About This Mac"],
    ["About 12 GB free disk", "models 10.7 GB (all recommended), Python packages, database", "df -h ~"],
    ["Internet for the downloads only", "tools and models are downloaded once; running needs no network and no API key", "-"],
    ["No admin rights needed", "every tool installs into the home folder; Postgres comes from a pip wheel", "-"]], [2.6, 3.0, 1.4]),
 P("3.2 What gets built", B),
 T([["Component", "What it does"],
    ["Ingestion (ragcap/ingest.py)", "Markdown, PDF (Docling when installed), Word, PowerPoint, HTML to text; paragraphs packed into ~180-word chunks; front-matter (doc, version, effective_date, superseded) becomes metadata and is removed before embedding; CSV/Excel become SQL tables; PNG/JPG drawings are described by a vision model"],
    ["Router", "classifies a question as documents, database or general and rewrites it as a standalone question using the chat history"],
    ["Document path", "retrieve top 6 chunks from pgvector, excluding superseded versions; grade each passage; one rewrite if none is kept; generate a cited answer or 'not in the knowledge base'"],
    ["Database path", "SQL agent writes one SELECT from the table's columns, sample rows and allowed values; it runs read-only with a 5 s timeout and one retry; a second step words the answer from the rows"],
    ["General path", "greetings and questions about the assistant; forbidden from stating facts"],
    ["Interfaces", "FastAPI (/health, /upload, /chat streaming one event per step, /eval), a static web page on /chat, a Gradio chat"],
    ["Evaluation", "frozen golden sets, eval.py, retrieval ablation b1_eval.py, data checks b1_check.py, scenarios.py, pid_eval.py"]], [1.7, 5.3]),
 P("3.3 Design decisions already built into the code", B),
 T([["Decision", "Why it is there"],
    ["Router prompt lists the uploaded tables and their columns; 'general' accepted only for greetings, thanks and questions about the assistant", "a single table pulls rule questions ('disk threshold') toward SQL; the guard stops facts from being answered without sources"],
    ["Standalone question copies the user's words and only resolves pronouns", "added words changed what retrieval found"],
    ["Grader asks one yes/no question per passage", "a 3B model cannot reliably pick indices out of six passages in one call"],
    ["SQL rules: WHERE only for conditions the question names; never GROUP BY the id; LIMIT 1 only for a single extreme; copy numbers exactly", "each rule fixes an observed wrong query or a garbled number"],
    ["JSON from the model is parsed leniently and never raises; model calls retry 3 times on connection errors", "one truncated reply must not end a 27-question run"],
    ["Version filter: WHERE d.superseded = false before the vector ORDER BY, on by default (VERSION_AWARE=1)", "an old version is 0.96-0.99 similar to the current one and is otherwise retrieved half the time (section 6.3)"]], [3.6, 3.4]),
 P("3.4 How results are kept honest", B),
 P("(1) The 27-question golden set was committed before any pipeline code existed, and the 25-question unseen set before its first run; git order is the evidence. (2) Golden questions are never pasted into prompts. (3) A scorer fix goes into golden/amendments.jsonl in its own commit (one entry: doc-008), never into the frozen file, and never after seeing a result it would change. (4) Every change is committed before it is measured, on the full set, and judged by the failing case ids. (5) Scores are reported over 3 repeated runs. (6) recreate.sh compares sha1 fingerprints of the frozen sets, the corpus and the drawings, and the ablation headline, and exits 1 on any difference."),
 P("4. Preparation: install the tools (once per Mac)", H2),
 P("Full detail, download locations and expected output: docs/INSTALL_AND_USE.md (PDF INSTALL_ragcap.pdf). In short:"),
 C("""
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.zshrc     # uv into ~/.local/bin
uv python install 3.12                                                  # python3.12 (arm64)
mkdir -p ~/.local/opt/ollama && cd ~/.local/opt/ollama
curl -fsSL -o ollama-darwin.tgz https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz
tar xzf ollama-darwin.tgz && rm ollama-darwin.tgz && ln -sf ~/.local/opt/ollama/ollama ~/.local/bin/ollama
mkdir -p ~/.ollama && nohup ollama serve > ~/.ollama/serve.log 2>&1 &
ollama pull llama3.2:3b && ollama pull nomic-embed-text                # required, 2.3 GB
ollama pull qwen3:8b                                                    # recommended grader, 5.2 GB
ollama pull qwen2.5vl:3b                                                # only for drawings, 3.2 GB
"""),
 P("Verify: python3.12 --version prints 3.12.x; ollama --version prints 0.40.x; ollama list shows the pulled models."),
 P("5. Implementation", H2),
 P("All commands run in the build folder. ./recreate.sh performs 5.1 to 5.3 and the checks of section 6.2 in one go; doing them by hand shows what each part does.", B),
 P("<b>5.1 Settings and Python environment.</b>", B),
 C("""
PW=$(openssl rand -hex 12)
printf 'PGHOST=localhost\\nPGPORT=5433\\nPGUSER=ragcap\\nPGPASSWORD=%s\\nPGDATABASE=ragcap\\n' "$PW" > .env; chmod 600 .env
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-local-pg.txt
.venv/bin/python -c "import langgraph, psycopg, pgserver, platform; print('ok', platform.machine())"   # ok arm64
"""),
 P("<b>5.2 Database and schema.</b> pgctl.sh creates the database on first start with the password from .env and runs it natively (it would use a Docker container instead if the docker command existed). The server listens on TCP only: its Unix socket is off because the project path is longer than macOS's 103-byte socket limit, which otherwise stops the server from starting.", B),
 C("""
./pgctl.sh start && ./pgctl.sh status                       # pg_ctl: server is running
./pgctl.sh psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
./pgctl.sh psql -tAc "select extversion from pg_extension where extname='vector'"     # 0.6.2
.venv/bin/python step1_check.py                             # applies schema.sql, stores and finds two embeddings
   embedding dim: 768 / nearest: Kafka consumer lag alert threshold 0.383 / STEP 1 OK
"""),
 P("schema.sql: documents (name, version, superseded, effective_date, source_path), chunks (text, embedding vector(768), meta jsonb, HNSW cosine index), uploaded_tables (tables the SQL agent may query). pgvector 0.6.2 has no hnsw.iterative_scan, so retrieve() sets hnsw.ef_search = 1000 instead; a filtered search therefore still returns 6 chunks on a larger table."),
 P("<b>5.3 Ingest the corpus and the table.</b> The corpus is 8 Kafka runbooks, each in an old (superseded) and a current version, plus one CSV table.", B),
 C("""
.venv/bin/python -m ragcap.ingest data/docs_versioned        # 16 documents, 1 chunk each
.venv/bin/python -m ragcap.ingest data/tables                # broker_inventory: 6 rows, 6 columns
./pgctl.sh psql -tAc "select count(*) from documents"        # 16; chunks 16; superseded 8; uploaded_tables 1
"""),
 P("<b>5.4 The graph</b> (ragcap/graph.py). State: question, history, route, standalone question, chunks, relevant chunks, rewrite count, SQL, rows, answer, and a per-step trace (milliseconds, tokens).", B),
 T([["Step", "What it does", "LLM calls"],
    ["router", "JSON {route, standalone}; sees the table names and columns; guard on 'general'", "1"],
    ["retrieve", "embeds the standalone question; cosine search in pgvector; top 6; WHERE superseded = false when VERSION_AWARE=1", "0 (1 embedding)"],
    ["grade", "one yes/no call per passage (3 in parallel); with GRADE_MODE=escalate, if nothing is kept, one qwen3:8b call reads all six", "6 (+1)"],
    ["rewrite", "one expanded query, allowed once, then retrieve and grade again", "1"],
    ["generate", "answer with [n] citations; 'not in the knowledge base' without an LLM call if nothing is relevant", "0-1"],
    ["sql_agent", "one SELECT validated (no ';', no write keywords), READ ONLY transaction, 5 s statement timeout, one retry with the error", "1-2"],
    ["generate_sql", "plain-language answer from the rows, numbers copied exactly", "1"],
    ["general", "short reply, no facts", "1"]], [1.1, 4.9, 1.0]),
 C("""
.venv/bin/python try.py "Thanks!" "How many brokers are in rack-b?" "At what disk utilisation should a broker page?"
   route=general  ... You're welcome!     route=database ... There are 2 brokers in rack-b.
   route=documents ... exceeds 75%.        (each 0.3-1.5 s)
"""),
 P("<b>5.5 Interfaces.</b>", B),
 C("""
# web page at http://127.0.0.1:8000/ ; API: GET /health, POST /upload, POST /chat (streaming)
.venv/bin/uvicorn api:app --port 8000
.venv/bin/python ui.py                     # Gradio, http://127.0.0.1:7860
"""),
 P("<b>5.6 P&amp;ID drawings.</b> pid/make_pid.py draws three synthetic P&amp;IDs from one template and writes their ground truth (39 tags, every valve and instrument relation) and 12 frozen questions. Ingesting a PNG asks the vision model for one fact per sentence (title block, equipment, valves and what they sit between, instruments and what they measure); that text is embedded like any document and the image path is kept in the chunk's metadata.", B),
 C("""
.venv/bin/python pid/make_pid.py                               # deterministic drawings + ground truth + questions
.venv/bin/python -m ragcap.ingest pid/drawings                 # ~25 s with qwen2.5vl:3b
"""),
 P("<b>5.7 Docling (optional).</b> Layout-aware parsing for PDF, Word, PowerPoint and HTML, kept in its own environment so the main one stays small. ingest.py uses Docling if it is importable, otherwise .venv-docling as a subprocess, otherwise pypdf text for PDFs. Measured: a 7-page PDF converted in ~47 s with its tables kept as Markdown tables (torch 2.14.1 on the Metal backend).", B),
 C("""
uv venv --python 3.12 .venv-docling && uv pip install --python .venv-docling/bin/python docling
"""),
 P("<b>5.8 Operations scripts.</b>", B),
 T([["Script", "Use"],
    ["pgctl.sh", "the database: start, stop, status, ready, psql, dump, restore, reset"],
    ["services.sh", "start, stop [--all], status, check (the clean-start check of 6.1)"],
    ["recreate.sh", "rebuild from zero and verify every fingerprint (6.2); resets the database to the 16-document baseline"],
    ["scenarios.py", "the scenario catalogue with expected answers (6.4)"],
    ["run_series.sh, summarize_series.py", "repeated evaluation runs and their mean, range and failing ids (6.5)"]], [2.0, 5.0]),
 P("<b>5.9 Choose the model profile.</b> Lean is the default. The recommended profile adds qwen3:8b as a second-opinion grader (sections 6.5 and 6.10); turn it on with three lines in .env and restart the web page or Gradio:", B),
 C("""
GRADE_MODEL=qwen3:8b
GRADE_MODE=escalate
GRADE_MAX_TOKENS=600
"""),
 P("6. Testing", H2),
 P("<b>6.1 Clean start.</b> Proves the whole path works after a reboot or sleep. Tested from a fully stopped state (results/clean_start_20261023.log):", B),
 C("""
$ ./services.sh stop --all      postgres: stopped / ollama: stopped
$ ./services.sh check           FAIL postgres not ready; FAIL ollama not running; CLEAN START FAILED (2)  [exit 1]
$ ./services.sh start           ollama: started (Ollama 0.40.9); postgres: running
$ ./services.sh check           PASS python venv 3.12.15 arm64 | PASS .env mode 600 | PASS postgres ready
                                PASS pgvector 0.6.2 | PASS data 16 docs, 16 chunks, 8 superseded, 1 tables
                                PASS ollama, llama3.2:3b, nomic-embed-text
                                PASS smoke general 302 ms, database 575 ms, documents 748 ms
                                PASS api /health | PASS web page / HTTP 200 | CLEAN START OK  [exit 0]
"""),
 P("<b>6.2 Rebuild and fingerprints.</b> ./recreate.sh ends RECREATE OK. Checked: database counts 16 docs, 16 chunks, 8 superseded, 1 table; golden.jsonl sha1 68ec09bd..., golden_heldout.jsonl 02ddcfd6..., amendments.jsonl 36a0e6e0..., corpus c2b025608d03; P&amp;ID questions, ground truth and the three drawings byte for byte; data checks PASS with all three injected faults reported (old version marked current, version stored as text, banner in embedded text); pair similarity old vs current 0.963-0.990, old version ranked first for 1 of 8 plain questions.", B),
 P("<b>6.3 Version filter, retrieval level</b> (b1_eval.py: 32 frozen document cases, 12 version traps and 20 controls, no LLM, deterministic):", B),
 T([["Metric", "Filter OFF", "Filter ON"],
    ["Superseded chunks retrieved", "99/192 (51.6%)", "0/192 (0.0%)"],
    ["Trap cases passing (facts present, no stale value from an old chunk)", "2/12", "12/12"],
    ["Trap cases with the stale value arriving from an old chunk", "10/12", "0/12"],
    ["Stale string anywhere in context (the current runbook quotes its former value)", "10/12", "6/12"],
    ["Control cases passing (must stay flat)", "20/20", "20/20"],
    ["Median retrieve time, interleaved, 96 calls each", "12-13 ms", "12-13 ms (never more than 1 ms apart)"]], [4.0, 1.4, 1.6]),
 P("The latency varies by a millisecond from run to run, and every recreate.sh run rewrites results/ablation_summary.md, so this SOP quotes the range rather than one run."),
 P("<b>6.4 Scenario catalogue</b> (.venv/bin/python scenarios.py --with-drawings; results/scenarios_20261023_113645.md). KNOWN FAIL marks a documented weakness, listed in section 7.", B),
 T([["Id", "Question (settings)", "Result", "Answer / what it shows"],
    ["G1", "Thanks!", "PASS 0.3 s", "general agent, no facts"],
    ["G2", "largest message size our brokers accept?", "PASS 2.4 s", "nothing relevant, one rewrite, 'not in the knowledge base'"],
    ["D1", "consumer lag to raise an alert?", "PASS 1.6 s", "5,000 messages, cited (not the old 10,000)"],
    ["D2", "TLS port of BROKER-EAST-02?", "PASS 1.5 s", "9093 (not 9092)"],
    ["D3", "replication factor and default retention?", "KNOWN FAIL", "multi-hop: answers 3, misses 72 hours"],
    ["S1", "brokers above 85% disk usage?", "PASS 1.1 s", "brokers 3 and 5 (87.2%, 91.8%)"],
    ["S2", "broker with the most topics?", "KNOWN FAIL", "adds an unasked WHERE status='healthy'; says broker 2, 152"],
    ["S3", "total disk capacity in GB?", "PASS 0.7 s", "16,000 GB"],
    ["S4", "Delete all rows from the broker_inventory table.", "PASS 0.6 s", "model wrote DELETE; validator refused; table unchanged"],
    ["V1-OFF", "disk utilisation to page (VERSION_AWARE=0)", "observed", "75%: the old runbook is retrieved but this corpus's current runbook names its former value, so the model still answers right"],
    ["V1-ON", "same, filter on", "PASS 1.0 s", "75%"],
    ["V2", "who owns SEV-1 escalation?", "PASS 1.5 s", "Streaming Platform team (not Platform Reliability)"],
    ["R1", "highest disk usage and which broker?", "PASS 1.0 s", "91.8%, broker 5 (database route)"],
    ["R2", "minutes lag must stay high?", "KNOWN FAIL", "lean grader rejects the passage: 'not in the knowledge base'"],
    ["R2+", "same, recommended profile", "PASS 6.9 s", "5 minutes (qwen3:8b keeps the passage)"],
    ["U1", "which cloud provider hosts Kafka?", "PASS 2.5 s", "'not in the knowledge base' (refused, not guessed)"],
    ["M1", "valve isolating pump P-101 suction? (drawings)", "KNOWN FAIL", "'not in the knowledge base' although the drawing is retrieved"],
    ["M2", "controller and valve for flow into T-102?", "KNOWN FAIL", "'not in the knowledge base'"],
    ["W1", "browser: brokers above 85% on the web page", "PASS", "pills router 271 ms, sql_agent 399 ms, generate_sql 362 ms; brokers 3 and 5"]], [0.6, 2.4, 1.0, 3.0]),
 P("<b>6.5 Answer-level evaluation, repeated runs</b> (run_series.sh, 3 runs on each set; every configuration gave identical results in all three runs):", B),
 C("""
./run_series.sh m5 llama3.2:3b                                         # lean profile
GRADE_MODEL=qwen3:8b GRADE_MODE=escalate GRADE_MAX_TOKENS=600 N_HELD=3 N_ORIG=3 \\
  ./run_series.sh qwen3esc llama3.2:3b                                 # recommended profile
N_HELD=3 N_ORIG=3 ./run_series.sh llama8b llama3.1:8b                  # bigger answering model, all steps
.venv/bin/python summarize_series.py <label>                           # -> results/<label>_summary.md
"""),
 T([["Measure", "Lean (llama3.2:3b)", "Recommended (+ qwen3:8b grader)", "llama3.1:8b, all steps"],
    ["Unseen set (25): router / answers", "100% / 80.0%", "100% / 96.0%", "100% / 92.0%"],
    ["Unseen set: failing ids", "h-doc-01, -05, -13, -14, -15", "h-doc-15", "h-doc-14, h-una-02 (a refusal in other words)"],
    ["Unseen set: unanswerable refused", "2/2", "2/2", "1/2 as scored"],
    ["Tuned set (27): answers", "92.6% (doc-015, db-004)", "92.6% (doc-015, db-004)", "96.3% (db-004)"],
    ["Tuned set: multi-hop", "1/2", "1/2", "2/2"],
    ["Retrieval hit rate", "100%", "100%", "100%"],
    ["Time: document / database / general", "1.1 / 0.9 / 0.3 s", "3.0 / 0.9 / 0.3 s", "2.5 / 1.5 / 0.7 s"],
    ["Memory while answering", "~2.7 GB", "~2.7 GB, peak ~8.2 GB", "~5.5 GB"]], [1.9, 1.6, 1.8, 1.7]),
 P("Reading it: four of the five unseen failures in the lean profile are the 3B grader rejecting a correctly retrieved passage that is phrased differently from the question; the qwen3:8b second opinion fixes all four without making the system guess (both unanswerable questions are still refused). llama3.1:8b fixes multi-hop on the tuned set but is lower on the unseen set and always resident. h-una-02 is scored as a failure because the 8B model refused in other words ('not explicitly mentioned in the provided passages'); the frozen scorer is not changed after seeing a result."),
 P("<b>6.6 Version filter, answer level</b> (27-question set, LLM in the loop): filter OFF 88.9% (24/27), filter ON 92.6% (25/27). The difference is multi-hop, 0/2 to 1/2: with old versions excluded, the six retrieved chunks hold more distinct documents. Version questions are 8/8 both ways because each current runbook in this corpus names its former value; the retrieval-level proof (6.3) is the one that matters for a corpus without such sentences.", B),
 P("<b>6.7 P&amp;ID evaluation</b> (pid_eval.py: tags against ground truth, 12 questions through the full graph):", B),
 T([["Configuration", "Tags (of 39)", "Answers (of 12)", "Seconds per drawing", "Memory"],
    ["qwen2.5vl:3b, lean (default)", "38", "4", "5-12", "5.0 GB while ingesting"],
    ["qwen2.5vl:7b", "39", "6", "7-11", "7.7 GB while ingesting"],
    ["qwen2.5vl:7b + qwen3:8b grader", "39", "6", "-", "-"],
    ["qwen2.5vl:7b + llama3.1:8b answering", "39", "5", "-", "-"]], [2.5, 1.0, 1.1, 1.2, 1.2]),
 P("The right drawing is retrieved for 12/12 questions in every configuration, and the 7b descriptions are complete ('HV-101: Hand (isolation) valve between T-101 and P-101'). A stage probe showed the grader keeping the right drawing while the answer step still replied 'not in the knowledge base': the questions need reasoning over connections (which valve is on the suction side). Neither a bigger grader nor a bigger answering model fixes that; storing each drawing's connections as table rows the SQL agent can query is the next step (section 9)."),
 P("<b>6.8 Interfaces, upload, tracing.</b> In headless Chromium: the web page showed the three step pills and brokers 3 and 5 for 'Which brokers are above 85% disk usage?' (1035 ms); Gradio answered 75% with the trace 'router 265ms > retrieve 62ms > grade 437ms > generate 154ms' (screenshots in docs/img). POST /upload of a Markdown file returned it ingested and /health rose by one document. LangSmith opt-in: with LANGSMITH_TRACING=true, a bogus key and an unreachable endpoint, the question was still answered (exit 0) and the tracer only logged a connection warning; off by default.", B),
 P("<b>6.9 Backup and restore.</b> ./pgctl.sh dump > file then ./pgctl.sh restore < file kept all 16 chunks.", B),
 P("<b>6.10 Resources, measured</b> (resident size of Ollama's runner process with one model loaded; Ollama's own 'ollama ps' under-reports the vision models):", B),
 T([["Model", "Role", "Disk", "Memory", "Keep?"],
    ["llama3.2:3b", "all LLM steps", "2.0 GB", "2.4 GB", "required"],
    ["nomic-embed-text", "embeddings", "0.3 GB", "0.3 GB", "required (changing it means re-ingesting)"],
    ["qwen3:8b", "second-opinion grader", "5.2 GB", "5.5 GB", "recommended; loaded only for hard questions"],
    ["qwen2.5vl:3b", "drawings at ingest", "3.2 GB", "5.0 GB", "only if you ingest drawings"],
    ["llama3.1:8b, qwen2.5vl:7b", "tested in 6.5 and 6.7", "4.9 / 6.0 GB", "5.2 / 7.7 GB", "removed (ollama rm); not worth the memory"]], [1.6, 1.5, 0.9, 0.9, 2.1]),
 P("Ollama unloads a model after 5 minutes idle, so the recommended profile uses ~2.7 GB most of the time and ~8.2 GB for a few minutes after a hard question."),
 P("7. Known weaknesses (all reproducible with scenarios.py)", H2),
 T([["Weakness", "Cases", "Cause", "Lever"],
    ["Grader rejects a differently phrased passage", "R2, h-doc-01/05/13/14", "3B per-passage grader", "recommended profile (fixed: 80% to 96% unseen)"],
    ["Multi-hop: two facts from two documents", "D3, doc-015, h-doc-15", "grader keeps one of the two passages", "split the question and retrieve per part"],
    ["SQL adds an unasked condition or grouping", "S2, db-004", "3B model writing SQL", "a check that re-runs SQL with no extra WHERE when the result looks implausible"],
    ["P&ID relations", "M1, M2", "answer step does not infer connections", "connections as structured rows for the SQL agent"]], [2.0, 1.4, 1.7, 1.9]),
 P("8. Troubleshooting: problems met on this machine and their fixes", H2),
 T([["Symptom", "Cause", "Fix"],
    ["A copied .venv does not run (wrong architecture or a missing interpreter path)", "virtual environments are tied to the machine and user that made them", "mv .venv .venv-old; python3.12 -m venv .venv; pip install -r requirements.txt -r requirements-local-pg.txt"],
    ["pg_ctl: could not start server; log: Unix-domain socket path is too long", "macOS limits socket paths to 103 bytes; the project path is longer", "pgctl.sh starts the server with unix_socket_directories='' (TCP only)"],
    ["docker: command not found in every script", "Docker Desktop needs admin rights and is not installed", "pgctl.sh native backend; all scripts call pgctl.sh"],
    ["git: 'You have not agreed to the Xcode license agreements'", "the Xcode license is not accepted on this Mac", "sudo xcodebuild -license accept (needs an admin); git is only needed to commit or push"],
    ["uvicorn: address already in use on 8000", "another program owns port 8000", "lsof -nP -iTCP:8000 -sTCP:LISTEN; use --port 8765"],
    ["An evaluation stood still for 16 minutes, then finished", "the Mac went to idle sleep (pmset -g log: 'Entering Sleep state due to Idle Sleep')", "run long commands under caffeinate -i; the series scripts do it themselves"],
    ["P&ID summary named the wrong vision model", "ingest.py did not return the model name; pid_eval.py fell back to a fixed name", "fixed: ingest returns vision_model; check what ran with curl -s localhost:11434/api/ps"],
    ["results/pid_eval_summary.md shows a different run than expected", "every pid_eval.py run overwrites it", "copy it before an experiment (the default 3b run is kept as pid_eval_summary_m5_3b.md)"],
    ["'delete all brokers' routed to documents", "short imperative without the table name", "name the table; the SQL validator then refuses the DELETE (scenario S4)"],
    ["ollama ps shows 0.8 GB for a vision model", "Ollama under-reports vision runners", "measure with ps -axo rss,command | grep ollama"]], [2.3, 2.2, 2.5]),
 P("More symptoms, and the stage-by-stage probe for a wrong answer, are in the runbook (RUNBOOK_ragcap_operations.pdf, sections 5 and 7)."),
 P("9. Pending", H2),
 P("Deployment, at the end: (a) push the repository and publish the showcase site (git needs the Xcode license accepted); (b) Vercel: import the repository once in the Vercel dashboard (Framework 'Other', output directory site); (c) LangSmith: a real API key in .env. Improvements: (d) P&amp;ID connections as structured rows; (e) multi-hop by splitting a question; (f) an SQL plausibility retry (db-004); (g) real P&amp;ID drawings with their own golden questions; (h) Docling measured on a real PDF set."),
]
build("SOP_ragcap_build.pdf", "SOP: ragcap build", sop)

# ------------------------------------------------------------------ RUNBOOK
rb = [
 P("Runbook: operating and troubleshooting ragcap", H1),
 P("For whoever runs the system day to day on the Apple M5 Pro. Assumes the SOP has been completed. All commands run in the build folder."),
 P("1. Components and where they live", H2),
 T([["Component", "Where", "Notes"],
    ["Postgres 16.2 + pgvector 0.6.2", "pgctl.sh; data in .pgdata/; 127.0.0.1:5433, TCP only", "native from the pip wheel pgserver; does not start at login: ./services.sh start"],
    ["Ollama 0.40.9", "~/.local/opt/ollama (command ~/.local/bin/ollama); models in ~/.ollama/models; localhost:11434", "does not start at login: ./services.sh start; log ~/.ollama/serve.log"],
    ["Models", "llama3.2:3b, nomic-embed-text (required); qwen3:8b (recommended grader); qwen2.5vl:3b (drawings)", "override with LLM_MODEL, EMBED_MODEL, GRADE_*, VISION_MODEL in .env"],
    ["Credentials", ".env (mode 600, gitignored)", "never commit; never paste into chat or documents"],
    ["Code", "ragcap/ (config, db, llm, ingest, graph, vision, tracing), api.py, ui.py, try.py", "git repository in this folder"],
    ["Scripts", "services.sh, pgctl.sh, recreate.sh, scenarios.py, eval.py, run_series.sh, b1_check.py, b1_eval.py, pid_eval.py", "see section 3"],
    ["Traces and results", "traces.jsonl (one line per question, gitignored); results/", "m5_summary.md (lean), qwen3esc_summary.md (recommended), scenarios_*.md"]], [1.6, 3.0, 2.4]),
 P("2. Start, stop, health", H2),
 C("""
./services.sh start            # Ollama (ollama serve in the background) + Postgres; prints status
./services.sh status           # read-only: Ollama version and models in memory, Postgres counts, busy ports
./services.sh check            # clean-start check (2a): PASS/FAIL per item, CLEAN START OK or exit 1
./services.sh stop             # Postgres only (data kept in .pgdata/); --all also stops Ollama
.venv/bin/uvicorn api:app --port 8000 &   # web page + API; curl -s localhost:8000/health (8000 taken? --port 8765)
"""),
 P("/health returns the document count, chunk count and uploaded tables: 16, 16, [broker_inventory] at the baseline."),
 P("2a. Checking for a clean start", H2),
 P("Run after a reboot, after the Mac slept, after moving the folder, and before any evaluation series. It takes about 10 seconds and changes nothing except a temporary API on port 8765 and three lines in traces.jsonl."),
 T([["#", "Do", "Expect", "If not"],
    ["1", "./services.sh status", "ollama up, postgres up", "./services.sh start"],
    ["2", "./services.sh check", "every line PASS (---- lines are information) and CLEAN START OK; echo $? prints 0", "fix the first FAIL; the line says how"],
    ["3", "read the data line", "16 docs, 16 chunks, 8 superseded, 1 tables", "uploads or drawings were added: expected after use; ./recreate.sh restores the baseline before measuring"],
    ["4", "read the smoke lines", "general, database ('2' brokers), documents ('75'%) PASS, each under ~2 s (the first is slower while models load)", "section 7 stage probe"],
    ["5", "before a series", "caffeinate -i ./run_series.sh <label>; it refuses to start if a service is down", "section 2b"]], [0.3, 1.8, 2.9, 2.0]),
 P("2b. After a reboot or a sleep", H2),
 P("Neither the database nor the standalone Ollama starts on its own. ./services.sh start && ./services.sh check brings both back and proves the path works. A sleep pauses running work: on 2026-10-22 an eval.py started without caffeinate stood still for 16 minutes (pmset -g log showed 'Entering Sleep state due to Idle Sleep') and finished after the wake. Run long commands under caffeinate -i; run_series.sh, run_answer_ablation.sh and recreate.sh do it themselves."),
 P("3. Routine tasks", H2),
 T([["Task", "Command"],
    ["Ask a question from the shell", ".venv/bin/python try.py \"question\""],
    ["Web page / Gradio", ".venv/bin/uvicorn api:app --port 8000 then http://127.0.0.1:8000/ ; .venv/bin/python ui.py then http://127.0.0.1:7860"],
    ["Add documents", ".venv/bin/python -m ragcap.ingest <file-or-folder> [--version N]   (same name and version replaces it)"],
    ["Add a CSV/Excel table", ".venv/bin/python -m ragcap.ingest <file.csv>   (table name from the file name; Excel: one table per sheet)"],
    ["Add a drawing (P&ID)", ".venv/bin/python -m ragcap.ingest <file.png>   (5-12 s per drawing with qwen2.5vl:3b)"],
    ["Add a new version of a document", "give it front-matter (doc, version, effective_date, superseded) and ingest; mark the old row: UPDATE documents SET superseded=true WHERE name=... AND version<N; then b1_check.py --no-trap"],
    ["Version filter", "on by default; VERSION_AWARE=0 only for the ablation; never set 0 in .env"],
    ["Use the recommended grader", "add GRADE_MODEL=qwen3:8b, GRADE_MODE=escalate, GRADE_MAX_TOKENS=600 to .env; restart the web page or Gradio"],
    ["Run the scenario catalogue", ".venv/bin/python scenarios.py [--with-drawings]   (about 1 minute; exit 1 only on an unexpected failure)"],
    ["Run an evaluation", "caffeinate -i .venv/bin/python eval.py [--golden golden/golden_heldout.jsonl] [--tag name]   (under 1 minute)"],
    ["Run a series", "./run_series.sh <label> <model>; .venv/bin/python summarize_series.py <label>   (about 3-7 minutes)"],
    ["Re-prove the version filter", ".venv/bin/python b1_eval.py --latency 3   (results/ablation_summary.md)"],
    ["Re-run the P&ID evaluation", "copy results/pid_eval_summary.md first, then .venv/bin/python pid_eval.py [--ingest]"],
    ["Rebuild to the baseline", "./recreate.sh   (RECREATE OK; resets the database to the 16 documents)"],
    ["Models in memory / free them", "./services.sh status or ollama ps; ollama stop <model>; idle models unload after 5 minutes"],
    ["Inspect recent traces", "tail -n 3 traces.jsonl | .venv/bin/python -m json.tool"],
    ["List what is stored", "./pgctl.sh psql -c \"select d.name,d.version,count(c.id) from documents d join chunks c on c.doc_id=d.id group by 1,2\""]], [1.9, 5.1]),
 P("4. Backup, restore, reset", H2),
 C("""
./pgctl.sh dump > ragcap_$(date +%Y%m%d).dump      # backup before re-ingesting or changing the embedding model
./pgctl.sh restore < ragcap_YYYYMMDD.dump           # restore (verified: all 16 chunks back)
./pgctl.sh reset                                     # DESTROYS .pgdata/; then ./recreate.sh
"""),
 P("Dump files contain document text: keep them out of git. Take a dump before any reset."),
 P("5. Troubleshooting", H2),
 T([["Symptom", "Likely cause", "Fix"],
    ["services.sh check: FAIL in the first lines, smoke tests skipped", "a service is down, or the venv or .env is missing", "the FAIL line names the fix; usually ./services.sh start"],
    ["Connection refused on 5433", "the database is stopped", "./pgctl.sh start; details in .pgdata/server.log"],
    ["Connection refused on 11434", "Ollama is stopped", "./services.sh start"],
    ["password authentication failed", ".env changed after the database was created", "restore the old .env, or ./pgctl.sh reset and ./recreate.sh"],
    ["pg_ctl: could not start server", "port 5433 in use, or a stale lock after a crash", "lsof -nP -iTCP:5433; read .pgdata/server.log"],
    ["address already in use (web page or Gradio)", "another program owns the port", "--port 8765, or GRADIO_SERVER_PORT=7861 .venv/bin/python ui.py"],
    ["A run stood still, then finished much later", "the Mac slept", "caffeinate -i; section 2b"],
    ["Everything answers 'not in the knowledge base'", "nothing ingested, or the grader rejects everything", "check /health; stage probe (section 7); try the recommended grader"],
    ["Right passage retrieved but 'not in the knowledge base'", "the 3B grader rejected it", "recommended grader; stage probe"],
    ["Answers quote a retired value", "VERSION_AWARE is off, or the old row is not marked superseded", "./pgctl.sh psql -c \"select name,version,superseded from documents\"; b1_check.py"],
    ["Same question gives a different SQL query", "3B model variability", "read the sql field in traces.jsonl; judge changes over 3 runs"],
    ["'only a single read-only SELECT is allowed'", "the model wrote a write statement", "expected safety behaviour"],
    ["AssertionError: EMBED_DIM does not match", "the embedding model changed", "change EMBED_DIM and vector(N) together, recreate the chunks table, re-ingest"],
    ["Image ingest fails", "vision model not pulled", "ollama pull qwen2.5vl:3b"],
    ["Memory pressure", "several models resident", "ollama ps; ollama stop <model>; section 6"],
    ["git refuses to run (Xcode license)", "license not accepted", "sudo xcodebuild -license accept (admin)"],
    ["First request after idle takes several seconds", "Ollama loading the model", "expected; later requests are fast"]], [2.1, 2.2, 2.7]),
 P("6. Models and memory", H2),
 T([["Profile", "Models", "Disk", "Memory", "Unseen / tuned answers"],
    ["Lean (default)", "llama3.2:3b + nomic-embed-text", "2.3 GB", "~2.7 GB", "80% / 92.6%"],
    ["Recommended", "Lean + qwen3:8b grader", "7.5 GB", "~2.7 GB, peak ~8.2 GB", "96% / 92.6%"],
    ["With drawings", "Recommended + qwen2.5vl:3b", "10.7 GB", "+5.0 GB while ingesting", "P&ID 38/39 tags"]], [1.3, 2.0, 0.8, 1.5, 1.4]),
 C("""
ollama list                     # installed models and disk size
ollama ps                       # models in memory now (under-reports vision models)
ollama stop qwen3:8b            # free memory now
ollama rm <model>               # free disk; ollama pull <model> restores it
"""),
 P("7. Debugging a wrong answer, stage by stage", H2),
 C("""
.venv/bin/python - <<'EOF'
import ragcap.graph as g
s = g.router({"question": "YOUR QUESTION", "history": [], "trace": []})
print(s["route"], "|", s["standalone"])           # 1. route and standalone question
r = g.retrieve({**s}); print([(c["doc"], c["dist"]) for c in r["chunks"]])   # 2. is the right document in the top 6?
gr = g.grade({**s, **r, "trace": []}); print([c["doc"] for c in gr["relevant"]])  # 3. did grade keep it?
EOF
"""),
 P("The first stage that goes wrong is the one to fix. A retrieval problem shows as the wrong document or a high distance; a grading problem as an empty relevant list while the right document was retrieved; an answer problem as the right document kept and a wrong answer."),
 P("8. Security notes", H2),
 P("- The database and Ollama listen on localhost only; the database has no Unix socket. - The SQL agent runs one SELECT/WITH statement in a READ ONLY transaction with a 5 s timeout, but as the user that owns the tables; beyond a local demo give it a separate read-only role. - /upload has no authentication or size limit; keep the API on localhost. - Uploaded text goes to the model unfiltered, so a malicious document can attempt prompt injection."),
 P("9. Evaluation pass/fail guide (M5 baselines)", H2),
 T([["Metric", "Lean baseline", "Recommended baseline", "Accept a change if"],
    ["Router accuracy, tuned / unseen", "100% / 100%", "100% / 100%", "no drop"],
    ["Answers correct, tuned / unseen", "92.6% / 80.0%", "92.6% / 96.0%", "no drop on either set, over 3 runs"],
    ["Retrieval hit rate", "100%", "100%", ">= 95%"],
    ["Unanswerable refused", "4/4 (both sets)", "4/4", "never regress"],
    ["Scenario catalogue", "12 pass, 0 unexpected", "-", "0 unexpected failures"],
    ["Superseded chunks, filter ON", "0/192", "0/192", "stays 0"]], [2.0, 1.5, 1.6, 1.9]),
 P("Judge a change on the failing case ids, not only the percentage. Never edit golden/golden.jsonl or golden_heldout.jsonl to make a run pass."),
 P("10. Rebuilding elsewhere", H2),
 P("docs/INSTALL_AND_USE.md (PDF INSTALL_ragcap.pdf) installs everything by hand; docs/RECREATE.md (PDF RECREATE_ragcap.pdf) is the from-zero guide with the scenario catalogue and the fingerprints; ./recreate.sh runs it unattended and exits 1 on any mismatch. Run it after any change to the corpus, the schema or retrieve()."),
 P("11. The showcase site", H2),
 P("site/ is static: results, the flow, screenshots, the documents, and a replay of recorded runs (site/data/replay.json, rebuilt from results/ by site/build_replay.py). It is updated locally; publishing (./publish_site.sh, which pushes the gh-pages branch) and Vercel wait for the deployment stage. Never put the database password, traces or dumps in site/."),
 P("12. Change control for prompt or pipeline changes", H2),
 T([["#", "Action", "Command / rule"],
    ["1", "Reproduce the failure on one question", ".venv/bin/python try.py \"question\" ; then the stage probe (section 7)"],
    ["2", "Find the first stage that goes wrong", "router -> retrieve -> grade -> generate (or sql_agent -> generate_sql)"],
    ["3", "Change ONE prompt or rule", "edit ragcap/graph.py; never paste golden questions into prompts"],
    ["4", "Probe the question plus 3 neighbours", ".venv/bin/python try.py ... (watch for the fix leaking into other queries)"],
    ["5", "Commit before measuring", "git add -A && git commit -m \"what and why\" (git needs the Xcode license accepted)"],
    ["6", "Measure", "./run_series.sh <label> llama3.2:3b; .venv/bin/python scenarios.py"],
    ["7", "Compare by failing ids", "results/<label>_summary.md against results/m5_summary.md"],
    ["8", "Record it", "add the result to the SOP, then python docs/build_pdfs.py (needs reportlab)"]], [0.3, 2.6, 4.1]),
]
build("RUNBOOK_ragcap_operations.pdf", "Runbook: ragcap operations", rb)

# ------------------------------------------------------------------ RECREATE (rendered from docs/RECREATE.md, the source of truth)
def inline(t):
    t = escape(t)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="7.5">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def md_to_story(md: str):
    story, lines, i = [], md.splitlines(), 0
    H3 = ParagraphStyle("H3", parent=H2, fontSize=11, spaceBefore=8)
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            story.append(C("\n".join(lines[i + 1:j]))); i = j + 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-+", c) for c in cells):
                    rows.append(cells)
                i += 1
            n = len(rows[0]); w = 7.0 / n
            widths = [w] * n
            if n == 5: widths = [0.45, 1.9, 1.6, 1.5, 1.55] if rows[0][0] == "Id" else [1.25, 1.75, 1.95, 0.75, 1.3]
            if n == 3: widths = [1.6, 2.6, 2.8]
            if n == 2: widths = [2.0, 5.0]
            data = [[Paragraph(inline(c), SM) for c in r] for r in rows]
            t = Table(data, colWidths=[x * inch for x in widths], repeatRows=1)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dde6f0")),
                                   ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(t); story.append(Spacer(1, 4)); continue
        if ln.startswith("# "): story.append(P(inline(ln[2:]), H1))
        elif ln.startswith("## "): story.append(P(inline(ln[3:]), H2))
        elif ln.startswith("### "): story.append(P(inline(ln[4:]), H3))
        elif re.match(r"^\d+\. ", ln) or ln.startswith("- "): story.append(P("&nbsp;&nbsp;" + inline(ln), B))
        elif ln.strip(): story.append(P(inline(ln), B))
        i += 1
    return story


import re
md = open(os.path.join(OUT, "RECREATE.md")).read()
build("RECREATE_ragcap.pdf", "Recreate ragcap", md_to_story(md))
# the hand-install guide, rendered the same way from docs/INSTALL_AND_USE.md
build("INSTALL_ragcap.pdf", "Install and use ragcap", md_to_story(open(os.path.join(OUT, "INSTALL_AND_USE.md")).read()))
print("ok")
