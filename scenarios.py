"""Run the scenario catalogue (docs/RECREATE.md section 3) and record what happened.

    .venv/bin/python scenarios.py                   # 16 question scenarios (W1, the web page, is a browser test)
    .venv/bin/python scenarios.py --with-drawings   # also M1/M2: ingests pid/drawings first if they are not loaded

Each scenario runs in its own process so its settings (VERSION_AWARE, GRADE_MODE ...) apply exactly as in a shell.
A scenario passes when the route is right, every expected fact is in the answer and no forbidden value is.
Scenarios marked known=... are documented weaknesses: they are reported as KNOWN FAIL, and as KNOWN FIXED if they pass.
Exit 1 only on an unexpected failure. Writes results/scenarios_<ts>.json and .md.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ESCALATE = {"GRADE_MODEL": "qwen3:8b", "GRADE_MODE": "escalate", "GRADE_MAX_TOKENS": "600"}

# id, question, settings, expected route, facts (all required; "a|b" = either), forbidden, what it shows, known weakness
S = [
    ("G1", "Thanks!", {}, "general", [], [], "general agent: no facts, 2 LLM calls", None),
    ("G2", "What is the largest message size our brokers accept?", {}, "documents", ["not in the knowledge base"], [],
     "grade finds nothing, one rewrite, then an explicit refusal", None),
    ("D1", "At what consumer lag should operations raise an alert?", {}, "documents", ["5,000|5000"], ["10,000|10000"],
     "normal document flow with a citation", None),
    ("D2", "What port does BROKER-EAST-02 use for TLS traffic?", {}, "documents", ["9093"], ["9092"],
     "exact-string lookup (control case for the version filter)", None),
    ("D3", "What replication factor and what default retention apply to a new standard production topic?", {}, "documents",
     ["3", "72"], [], "multi-hop: two facts from two documents", "multi-hop: the per-passage grader keeps one of the two passages"),
    ("S1", "Which brokers are above 85% disk usage?", {}, "database", ["87.2", "91.8"], [], "SQL agent with a WHERE from the question", None),
    ("S2", "Which broker hosts the most topics, and how many?", {}, "database", ["210"], [],
     "ORDER BY ... LIMIT 1 for a single extreme", "SQL: the 3B model sometimes groups by rack (db-004)"),
    ("S3", "What is the total disk capacity across all brokers in GB?", {}, "database", ["16,000|16000"], [],
     "SUM, numbers copied exactly", None),
    ("S4", "Delete all rows from the broker_inventory table.", {}, "database", ["only a single read-only SELECT is allowed"], [],
     "the model writes a DELETE; the validator rejects it and the table is unchanged", None),
    ("V1-OFF", "At what disk utilisation should a broker page?", {"VERSION_AWARE": "0"}, "documents", [], [],
     "the trap: with the filter off the retired 85% can come back (observed, not scored)", None),
    ("V1-ON", "At what disk utilisation should a broker page?", {"VERSION_AWARE": "1"}, "documents", ["75"], [],
     "the fix: superseded versions excluded before ranking", None),
    ("V2", "Which team owns escalation for a SEV-1 Kafka incident?", {"VERSION_AWARE": "1"}, "documents",
     ["Streaming Platform"], ["Platform Reliability"], "a version conflict with no number in it", None),
    ("R1", "What is the highest disk usage percentage and which broker has it?", {}, "database", ["91.8"], [],
     "router ambiguity: a rule in a runbook vs a measurement in the table", None),
    ("R2", "How many minutes must consumer lag stay high before the alert fires?", {}, "documents", ["5 minutes|5 min"], [],
     "lean profile: the 3B grader rejects a differently phrased passage", "grader: needs the second-opinion grader (R2+)"),
    ("R2+", "How many minutes must consumer lag stay high before the alert fires?", ESCALATE, "documents", ["5 minutes|5 min"], [],
     "recommended profile: qwen3:8b second opinion keeps the passage", None),
    ("U1", "Which cloud provider hosts the Kafka cluster?", {}, "documents", ["not in the knowledge base"], [],
     "unanswerable: refused, not guessed", None),
]
M = [
    ("M1", "Which valve isolates the suction of pump P-101?", {}, "documents", ["HV-101"], ["HV-102"],
     "a drawing answered through its vision description", "P&ID relations: the answer step does not infer 'suction side'"),
    ("M2", "Which instrument controls the flow into tank T-102, and through which valve?", {}, "documents",
     ["FIC-101", "FCV-101"], [], "the hardest tag family for a 3B vision model", "P&ID relations: the answer step does not chain controller and valve"),
]

RUNNER = r"""
import json, sys
from ragcap.graph import ask
o = ask(sys.argv[1])
print("\x1eJSON" + json.dumps({"route": o.get("route"), "answer": o.get("answer", ""), "sql": o.get("sql"),
      "path": [t["node"] for t in o.get("trace", [])], "total_ms": o.get("total_ms")}))
"""


def has(text, fact):
    return any(alt.strip().lower() in text.lower() for alt in fact.split("|"))


def run_one(q, env):
    e = {**os.environ, **env}
    p = subprocess.run([sys.executable, "-c", RUNNER, q], cwd=ROOT, env=e, capture_output=True, text=True, timeout=600)
    out = p.stdout.split("\x1eJSON")[-1] if "\x1eJSON" in p.stdout else None
    return json.loads(out) if out else {"route": "error", "answer": (p.stderr or "")[-300:], "path": [], "total_ms": None}


def ensure_drawings():
    from ragcap.db import connect
    if connect().execute("select count(*) from documents where name like 'PID-%'").fetchone()[0] < 3:
        print("ingesting pid/drawings (vision model, about 25 s on Apple Silicon) ...")
        from ragcap.ingest import ingest_path
        ingest_path(ROOT / "pid" / "drawings")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--with-drawings", action="store_true"); a = ap.parse_args()
    cases = S + (M if a.with_drawings else [])
    if a.with_drawings:
        ensure_drawings()
    from ragcap.db import connect
    rows_before = connect().execute("select count(*) from broker_inventory").fetchone()[0]
    rows, unexpected = [], 0
    for sid, q, env, route, facts, forbidden, shows, known in cases:
        o = run_one(q, env)
        ok = o["route"] == route and all(has(o["answer"], f) for f in facts) and not any(has(o["answer"], f) for f in forbidden)
        if sid == "S4":
            ok = ok and connect().execute("select count(*) from broker_inventory").fetchone()[0] == rows_before
        if sid == "V1-OFF":
            status = "OBSERVED"
        elif ok:
            status = "KNOWN FIXED" if known else "PASS"
        else:
            status = "KNOWN FAIL" if known else "FAIL"
        unexpected += status == "FAIL"
        rows.append({"id": sid, "question": q, "settings": env, "expected_route": route, "route": o["route"], "status": status,
                     "path": o["path"], "total_ms": o["total_ms"], "answer": o["answer"], "sql": o.get("sql"),
                     "shows": shows, "known": known})
        print(f"{sid:<7} {status:<11} route={o['route']:<9} {o['total_ms'] or 0:>6} ms  {o['answer'][:70]!r}")
    ts = time.strftime("%Y%m%d_%H%M%S")
    Path(ROOT / f"results/scenarios_{ts}.json").write_text(json.dumps(rows, indent=1))
    md = [f"# Scenario catalogue run {ts}", "",
          f"Settings per scenario as listed; default model {os.getenv('LLM_MODEL', 'llama3.2:3b')}. "
          f"{sum(r['status'] == 'PASS' for r in rows)} pass, {sum(r['status'] == 'KNOWN FAIL' for r in rows)} known weaknesses, "
          f"{sum(r['status'] == 'KNOWN FIXED' for r in rows)} known fixed, {unexpected} unexpected failures.", "",
          "| Id | Status | Route | Time | Answer (start) |", "|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['status']} | {r['route']} | {(r['total_ms'] or 0) / 1000:.1f} s | {r['answer'][:90].replace('|', '/').replace(chr(10), ' ')} |" for r in rows]
    Path(ROOT / f"results/scenarios_{ts}.md").write_text("\n".join(md) + "\n")
    print(f"\n{md[2]}\nsaved results/scenarios_{ts}.md")
    sys.exit(1 if unexpected else 0)


if __name__ == "__main__":
    main()
