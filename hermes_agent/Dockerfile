# Hermes Agent as a Home Assistant app (concept §8.2).
#
# The base is pinned by digest: upstream v0.22.5-desktop (multi-arch index,
# verified 2026-11-02). Do not change the pin without re-running the M0 gates.
FROM nousresearch/hermes-agent:v0.23.3-desktop@sha256:5f587d1c036e551f57f1c706c460b41a4f48de0c4763e5865343eafd3950a2bc

# The only software the app adds: the ingress web tier.
# The RUN below performs a build-time nginx syntax check with a throwaway
# fixture allowlist, which is removed in the same layer. The real allowlist is
# generated at container start by 40-ingress-access.
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY rootfs/ /

RUN set -eux; \
    mkdir -p /var/log/nginx /run/hermes-ingress; \
    chmod 0755 /etc/cont-init.d/40-ingress-access \
      /etc/cont-init.d/50-hermes-app-options \
      /usr/local/bin/hermes-app-seed \
      /usr/local/lib/hermes-ingress/access.py \
      /etc/s6-overlay/s6-rc.d/ingress-proxy/run; \
    chmod 0644 /usr/local/lib/hermes-ingress/access.py; \
    chmod 0755 /usr/local/lib/hermes-ingress; \
    mkdir -p /run/hermes-ingress; \
    printf 'allow 192.0.2.1;\ndeny all;\n' > /run/hermes-ingress/supervisor-access.conf; \
    nginx -t -c /etc/nginx/nginx.conf; \
    rm -f /run/hermes-ingress/supervisor-access.conf

LABEL org.opencontainers.image.title="Home Assistant App: Hermes Agent" \
      org.opencontainers.image.description="Self-hosted AI agent with dashboard, memory, skills and a shared browser" \
      org.opencontainers.image.source="https://github.com/thomaskonrad/hermes-agent-ha" \
      org.opencontainers.image.licenses="MIT"

# Liveness of the web tier (concept §9.4). Replaces the obsolete `watchdog`
# config key. It checks the dashboard the proxy fronts, directly on loopback:
# going through :8099 would always be refused by the Supervisor-source
# allowlist (loopback is not allowed), so it could never report healthy.
HEALTHCHECK --interval=120s --timeout=15s --start-period=120s --retries=2 \
    CMD curl -fsS -o /dev/null http://127.0.0.1:9119/api/status || exit 1

# Keep upstream's dispatcher (it runs s6-overlay's /init) and stay alive:
# HA has no command of its own to give us, and an empty CMD would make
# upstream's wrapper start the interactive TUI as the container's main program.
ENTRYPOINT ["/opt/hermes/docker/entrypoint-dispatch.sh"]
CMD ["sleep", "infinity"]
