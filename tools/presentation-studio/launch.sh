#!/usr/bin/env bash
# Desktop Mode: run this script with the installed game's presentations directory.
set -eu
studio_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
presentations="${1:-$studio_dir/../../mods/presentations}"
url=http://127.0.0.1:8735/tools/presentation-studio/index.html
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/2k5-presentation-studio-$UID.lock"
if ! flock -n 9; then
    xdg-open "$url"
    exit 0
fi
python3 "$studio_dir/serve.py" --presentations "$presentations" --no-browser &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
for attempt in {1..50}; do
    kill -0 "$server_pid" 2>/dev/null || { wait "$server_pid"; exit 1; }
    if curl --silent --fail "$url" >/dev/null; then
        xdg-open "$url" 9>&-
        wait "$server_pid"
        exit 0
    fi
    sleep 0.1
done
echo 'Presentation Studio did not start. See the error above.' >&2
exit 1
