#!/bin/bash
# Start, stop and check everything ragcap needs. Usage: ./services.sh start | stop [--all] | status | check
#   start   Ollama (the app if installed, else `ollama serve` in the background) and Postgres (pgctl.sh)
#   stop    Postgres; with --all also Ollama
#   status  one line per component, no changes made
#   check   clean-start check: PASS/FAIL per item, ends "CLEAN START OK" or exits 1. Read-only apart from a
#           temporary API on CHECK_PORT (default 8765) and a few questions (each appends one line to traces.jsonl)
cd "$(dirname "$0")"
OLLAMA_URL=http://localhost:11434
MODELS="llama3.2:3b nomic-embed-text"        # required; qwen2.5vl:3b (P&ID) and qwen3:8b (escalate grader) are optional
CHECK_PORT=${CHECK_PORT:-8765}
OLLAMA_BIN=$(command -v ollama || echo "$HOME/.local/bin/ollama")
FAILS=0
ok()   { printf '  PASS  %-26s %s\n' "$1" "$2"; }
bad()  { printf '  FAIL  %-26s %s\n' "$1" "$2"; FAILS=$((FAILS + 1)); }
info() { printf '  ----  %-26s %s\n' "$1" "$2"; }
ollama_up() { curl -sf "$OLLAMA_URL/api/version" >/dev/null; }
ollama_ver() { curl -s "$OLLAMA_URL/api/version" | sed -E 's/.*"version":"([^"]*)".*/Ollama \1/'; }

start_ollama() {
  ollama_up && { echo "ollama: already running ($(ollama_ver))"; return 0; }
  if [ -d /Applications/Ollama.app ]; then open -a Ollama
  else mkdir -p ~/.ollama; nohup "$OLLAMA_BIN" serve > ~/.ollama/serve.log 2>&1 & fi
  for i in $(seq 1 30); do ollama_up && break; sleep 1; done
  ollama_up && echo "ollama: started ($(ollama_ver))" || { echo "ollama: did not start, see ~/.ollama/serve.log" >&2; return 1; }
}

status() {
  echo "ragcap services ($(date '+%Y-%m-%d %H:%M:%S'))"
  if ollama_up; then
    have=$(curl -s $OLLAMA_URL/api/tags | .venv/bin/python -c "import sys,json; print(' '.join(m['name'] for m in json.load(sys.stdin)['models']))")
    loaded=$(curl -s $OLLAMA_URL/api/ps | .venv/bin/python -c "import sys,json; print(','.join(m['name'] for m in json.load(sys.stdin)['models']) or 'none')")
    echo "  ollama    up   $(ollama_ver)  models: $have  (in memory: $loaded)"
  else echo "  ollama    DOWN (./services.sh start)"; fi
  if ./pgctl.sh ready 2>/dev/null; then
    echo "  postgres  up   backend ${RAGCAP_PG:-$(command -v docker >/dev/null && echo docker || echo local)}, 127.0.0.1:$(sed -n 's/^PGPORT=//p' .env), $(./pgctl.sh psql -tAc "select (select count(*) from documents)||' docs, '||(select count(*) from chunks)||' chunks, '||(select count(*) from uploaded_tables)||' tables'")"
  else echo "  postgres  DOWN (./services.sh start)"; fi
  for p in 8000 7860 "$CHECK_PORT"; do
    who=$(lsof -nP -iTCP:"$p" -sTCP:LISTEN 2>/dev/null | awk 'NR==2{print $1" pid "$2}')
    [ -n "$who" ] && echo "  port $p listening: $who"
  done
  return 0
}

check() {
  echo "ragcap clean-start check ($(date '+%Y-%m-%d %H:%M:%S'))"
  # 1. environment
  if [ -x .venv/bin/python ] && .venv/bin/python -c "import psycopg, pgvector, langgraph, fastapi, gradio" 2>/dev/null; then
    ok "python venv" "$(.venv/bin/python -c 'import platform; print(platform.python_version(), platform.machine())')"
  else bad "python venv" ".venv missing or broken: ./recreate.sh"; fi
  if [ -f .env ]; then
    [ "$(stat -f %Lp .env)" = "600" ] && ok ".env" "present, mode 600" || bad ".env" "mode $(stat -f %Lp .env), expected 600: chmod 600 .env"
  else bad ".env" "missing: ./recreate.sh creates it"; fi
  # 2. database
  if ./pgctl.sh ready 2>/dev/null; then
    ok "postgres" "ready on 127.0.0.1:$(sed -n 's/^PGPORT=//p' .env)"
    v=$(./pgctl.sh psql -tAc "select extversion from pg_extension where extname='vector'" 2>/dev/null)
    [ -n "$v" ] && ok "pgvector extension" "$v" || bad "pgvector extension" "missing: ./pgctl.sh psql -c 'CREATE EXTENSION vector'"
    c=$(./pgctl.sh psql -tAc "select (select count(*) from documents)||' docs, '||(select count(*) from chunks)||' chunks, '||(select count(*) from documents where superseded)||' superseded, '||(select count(*) from uploaded_tables)||' tables'")
    if [ "$c" = "16 docs, 16 chunks, 8 superseded, 1 tables" ]; then ok "data (fingerprint)" "$c"
    elif [ -n "$c" ]; then info "data (fingerprint)" "$c (differs from 16/16/8/1: extra uploads or drawings; ./recreate.sh restores it)"
    else bad "data" "query failed"; fi
  else bad "postgres" "not ready: ./services.sh start"; fi
  # 3. models
  if ollama_up; then
    ok "ollama" "$(ollama_ver)"
    tags=$(curl -s $OLLAMA_URL/api/tags)
    for m in $MODELS; do echo "$tags" | grep -q "\"$m" && ok "model $m" "present" || bad "model $m" "missing: ollama pull $m"; done
    for m in qwen2.5vl:3b qwen3:8b; do echo "$tags" | grep -q "\"$m" && info "model $m" "present (optional)" || info "model $m" "absent (optional)"; done
  else bad "ollama" "not running: ./services.sh start"; fi
  [ "$FAILS" -gt 0 ] && { echo "  skipping smoke tests: fix the failures above first"; echo "CLEAN START FAILED ($FAILS)"; exit 1; }
  # 4. one question per route through the full graph
  .venv/bin/python - <<'EOF' || FAILS=$((FAILS + 1))
import sys, time
from ragcap.graph import ask
cases = [("Thanks!", "general", None),
         ("How many brokers are in rack-b?", "database", "2"),
         ("At what disk utilisation should a broker page?", "documents", "75")]
bad = 0
for q, route, fact in cases:
    t = time.perf_counter(); o = ask(q, []); ms = (time.perf_counter() - t) * 1000
    good = o["route"] == route and (fact is None or fact in o["answer"])
    bad += not good
    print(f"  {'PASS' if good else 'FAIL'}  {'smoke ' + route:<26} {ms:5.0f} ms  {o['answer'][:60]!r}")
sys.exit(1 if bad else 0)
EOF
  # 5. the API and the web page, on a temporary port
  if lsof -nP -iTCP:"$CHECK_PORT" -sTCP:LISTEN >/dev/null 2>&1; then bad "api" "port $CHECK_PORT busy: CHECK_PORT=<free port> ./services.sh check"
  else
    .venv/bin/uvicorn api:app --port "$CHECK_PORT" --log-level warning > /dev/null 2>&1 & API=$!
    for i in $(seq 1 30); do curl -sf "localhost:$CHECK_PORT/health" >/dev/null && break; sleep 0.5; done
    h=$(curl -sf "localhost:$CHECK_PORT/health"); w=$(curl -s -o /dev/null -w '%{http_code}' "localhost:$CHECK_PORT/")
    kill $API 2>/dev/null; wait $API 2>/dev/null
    [ -n "$h" ] && ok "api /health" "$h" || bad "api /health" "no answer on port $CHECK_PORT"
    [ "$w" = "200" ] && ok "web page /" "HTTP 200" || bad "web page /" "HTTP $w"
  fi
  [ "$FAILS" -eq 0 ] && echo "CLEAN START OK" || { echo "CLEAN START FAILED ($FAILS)"; exit 1; }
}

case "$1" in
  start)  start_ollama && ./pgctl.sh start && echo "postgres: running" && status ;;
  stop)   ./pgctl.sh stop && echo "postgres: stopped"
          if [ "$2" = "--all" ]; then
            if [ -d /Applications/Ollama.app ]; then osascript -e 'quit app "Ollama"'; else pkill -f "ollama serve"; fi
            sleep 2; ollama_up && echo "ollama: still running" || echo "ollama: stopped"
          fi ;;
  status) status ;;
  check)  check ;;
  *) echo "usage: ./services.sh start | stop [--all] | status | check" >&2; exit 2 ;;
esac
