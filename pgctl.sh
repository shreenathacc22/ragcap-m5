#!/bin/bash
# Postgres 16 + pgvector for ragcap, with two interchangeable backends. Usage: ./pgctl.sh start|stop|status|ready|psql [args]
#   docker: container ragcap-pg (pgvector/pgvector:pg16, volume ragcap_pgdata), used when the docker command exists
#   local:  native binaries from the pip wheel `pgserver` (Postgres 16.2 + pgvector 0.6.2, arm64 and x86_64 macOS),
#           data in .pgdata/, no Docker and no admin rights needed. Used when docker is absent.
# Force one with RAGCAP_PG=docker|local. Both listen on 127.0.0.1:$PGPORT with the user and password in .env.
set -e
cd "$(dirname "$0")"
[ -f .env ] || { echo "no .env: run ./recreate.sh first (it creates one)" >&2; exit 1; }
set -a; . ./.env; set +a
BACKEND=${RAGCAP_PG:-$(command -v docker >/dev/null && echo docker || echo local)}
PGDATA_DIR="$PWD/.pgdata"

local_bin() {
  [ -x .venv/bin/python ] || { echo "no .venv: run ./recreate.sh first" >&2; exit 1; }
  .venv/bin/python -c "import pgserver" 2>/dev/null || .venv/bin/python -m pip install -q -r requirements-local-pg.txt
  echo "$(.venv/bin/python -c 'import pgserver, os; print(os.path.dirname(pgserver.__file__))')/pginstall/bin"
}

case "$BACKEND:$1" in
  docker:start)
    if docker ps -a --format '{{.Names}}' | grep -qx ragcap-pg; then docker start ragcap-pg >/dev/null
    else docker run -d --name ragcap-pg -e POSTGRES_USER="$PGUSER" -e POSTGRES_PASSWORD="$PGPASSWORD" -e POSTGRES_DB="$PGDATABASE" \
           -p 127.0.0.1:"$PGPORT":5432 -v ragcap_pgdata:/var/lib/postgresql/data --restart unless-stopped pgvector/pgvector:pg16 >/dev/null
    fi
    for i in $(seq 1 30); do docker exec ragcap-pg pg_isready -q -U "$PGUSER" -d "$PGDATABASE" 2>/dev/null && break; sleep 1; done ;;
  docker:stop)   docker stop ragcap-pg >/dev/null ;;
  docker:status) docker ps -a --filter name=ragcap-pg --format '{{.Names}} {{.Status}}' ;;
  docker:ready)  docker exec ragcap-pg pg_isready -q -U "$PGUSER" -d "$PGDATABASE" ;;
  docker:psql)   shift; docker exec -i ragcap-pg psql -U "$PGUSER" -d "$PGDATABASE" "$@" ;;

  local:start)
    BIN=$(local_bin)
    if [ ! -f "$PGDATA_DIR/PG_VERSION" ]; then
      PWF=$(mktemp); printf '%s\n' "$PGPASSWORD" > "$PWF"
      "$BIN/initdb" -D "$PGDATA_DIR" -U "$PGUSER" --pwfile="$PWF" -A scram-sha-256 -E UTF8 --no-locale >/dev/null
      rm -f "$PWF"
    fi
    "$BIN/pg_isready" -q -h 127.0.0.1 -p "$PGPORT" && exit 0
    "$BIN/pg_ctl" -D "$PGDATA_DIR" -l "$PGDATA_DIR/server.log" -w \
      -o "-c listen_addresses=127.0.0.1 -p $PGPORT -c unix_socket_directories=''" start >/dev/null   # TCP only: deep paths exceed the 103-byte socket limit
    PGPASSWORD="$PGPASSWORD" "$BIN/psql" -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" -d postgres -tAc \
      "select 1 from pg_database where datname='$PGDATABASE'" | grep -q 1 || \
      PGPASSWORD="$PGPASSWORD" "$BIN/createdb" -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" ;;
  local:stop)    BIN=$(local_bin); "$BIN/pg_ctl" -D "$PGDATA_DIR" -m fast stop ;;
  local:status)  BIN=$(local_bin); "$BIN/pg_ctl" -D "$PGDATA_DIR" status | head -1 ;;
  local:ready)   BIN=$(local_bin); "$BIN/pg_isready" -q -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" ;;
  local:psql)    shift; BIN=$(local_bin); PGPASSWORD="$PGPASSWORD" "$BIN/psql" -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" "$@" ;;

  # backup to stdout / restore from stdin (custom format); reset DESTROYS every stored vector and table
  docker:dump)    docker exec ragcap-pg pg_dump -U "$PGUSER" -d "$PGDATABASE" -Fc ;;
  docker:restore) docker exec -i ragcap-pg pg_restore -U "$PGUSER" -d "$PGDATABASE" --clean --if-exists ;;
  docker:reset)   docker rm -f ragcap-pg && docker volume rm ragcap_pgdata ;;
  local:dump)     BIN=$(local_bin); PGPASSWORD="$PGPASSWORD" "$BIN/pg_dump" -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -Fc ;;
  local:restore)  BIN=$(local_bin); PGPASSWORD="$PGPASSWORD" "$BIN/pg_restore" -h 127.0.0.1 -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" --clean --if-exists ;;
  local:reset)    BIN=$(local_bin); "$BIN/pg_ctl" -D "$PGDATA_DIR" -m fast stop 2>/dev/null || true; rm -rf "$PGDATA_DIR" ;;

  *) echo "usage: ./pgctl.sh start|stop|status|ready|psql [args]|dump > file|restore < file|reset   (backend: $BACKEND)" >&2; exit 2 ;;
esac
