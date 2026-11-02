#!/bin/sh
# Live checks inside a running container (run via docker exec, see tests/).
# Prints HTTP codes; the caller asserts on them.
echo "--- dashboard direct (loopback, bypasses nginx) ---"
curl -s -o /dev/null -w "9119 http=%{http_code}\n" -m 5 http://127.0.0.1:9119/api/status || echo "9119 unreachable"
echo "--- ingress from loopback (NOT allowlisted: must be 403) ---"
curl -s -o /dev/null -w "8099 http=%{http_code}\n" -m 5 http://127.0.0.1:8099/api/status
echo "--- watchdog target from loopback (NOT allowlisted: must be 403) ---"
curl -s -o /dev/null -w "ha-health http=%{http_code}\n" -m 5 http://127.0.0.1:8099/ha-health
