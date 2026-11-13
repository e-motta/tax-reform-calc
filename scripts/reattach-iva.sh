#!/bin/bash
# Keep the IVA site on the finance VM's Caddy without editing the finance repo.
#
# The finance deploy checks out that repo's Caddyfile and recreates its Caddy
# container, which drops both this site block and the extra Docker network.
# Run this once after the steps in docs/deploy-oci.md, and again after a
# finance deploy. A systemd timer is included so the reattach is automatic.
#
# Installed path on the VM: /opt/caddy/reattach-iva.sh
# Site block:              /opt/caddy/iva-site.caddy
# Finance checkout:        /opt/portfolio-manager-v2/Caddyfile

set -euo pipefail

FINANCE_CADDYFILE="${FINANCE_CADDYFILE:-/opt/portfolio-manager-v2/Caddyfile}"
SITE_BLOCK="${SITE_BLOCK:-/opt/caddy/iva-site.caddy}"
MARKER="iva.eduardomotta.dev"
NETWORK="edge"

if [[ ! -f "$SITE_BLOCK" ]]; then
    echo "Missing site block: $SITE_BLOCK" >&2
    exit 1
fi
if [[ ! -f "$FINANCE_CADDYFILE" ]]; then
    echo "Missing finance Caddyfile: $FINANCE_CADDYFILE" >&2
    exit 1
fi

docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"

if ! grep -q "$MARKER" "$FINANCE_CADDYFILE"; then
    printf '\n' >> "$FINANCE_CADDYFILE"
    cat "$SITE_BLOCK" >> "$FINANCE_CADDYFILE"
    echo "Appended the IVA site block."
fi

caddy_id=$(docker ps -qf name=caddy | head -n 1)
if [[ -z "$caddy_id" ]]; then
    echo "No running Caddy container. Start the finance stack, then re-run." >&2
    exit 1
fi

if ! docker inspect "$caddy_id" --format '{{json .NetworkSettings.Networks}}' | grep -q "\"${NETWORK}\""; then
    docker network connect "$NETWORK" "$caddy_id"
    echo "Connected Caddy to ${NETWORK}."
fi

docker exec "$caddy_id" caddy reload --config /etc/caddy/Caddyfile
echo "Caddy reloaded."
