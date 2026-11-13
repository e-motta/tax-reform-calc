#!/bin/bash
# Forced command for the IVA deploy key. It is not the finance app's key.
#
#   restrict,command="/opt/tax-reform-calc/scripts/remote-deploy.sh" ssh-ed25519 ...
#
# SSH_ORIGINAL_COMMAND must be sha-<7-40 hex>. The script checks that commit
# out on origin/main, pulls that image, health-checks it, and rolls back to
# the previous image if the check fails.

set -euo pipefail

REPO_DIR="/opt/tax-reform-calc"
VENV_PYTHON="/opt/portfolio-venv/bin/python"
DEPLOY_ENV="/etc/iva/deploy.env"
DEPLOY_LOG="/opt/tax-reform-calc/deploy-history.log"
DEPLOY_LOCK="/var/run/iva-deploy.lock"
HEALTH_CHECK_HOST="iva.eduardomotta.dev"
HEALTH_CHECK_TIMEOUT=180
HEALTH_CHECK_INTERVAL=5
COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.production.yml)

log() {
    local timestamp
    timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "[$timestamp] $*" | tee -a "$DEPLOY_LOG"
}

log_error() {
    log "ERROR: $*" >&2
}

validate_tag() {
    local tag="$1"
    if [[ ! "$tag" =~ ^sha-[0-9a-f]{7,40}$ ]]; then
        log_error "Invalid tag format: '$tag'"
        log_error "Expected format: sha-<7-40 hex characters>"
        exit 1
    fi
}

get_app_container_id() {
    cd "$REPO_DIR"
    docker compose "${COMPOSE_FILES[@]}" ps -q iva 2>/dev/null || echo ""
}

get_current_tag() {
    local container_id image
    container_id=$(get_app_container_id)
    if [[ -z "$container_id" ]]; then
        echo ""
        return
    fi
    image=$(docker inspect --format='{{.Config.Image}}' "$container_id" 2>/dev/null || echo "")
    echo "${image##*:}"
}

get_container_health() {
    local container_id
    container_id=$(get_app_container_id)
    if [[ -n "$container_id" ]]; then
        docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

check_network_aliases() {
    log "Checking network aliases on edge network..."
    local container_id aliases service_name
    container_id=$(docker ps -qf name=iva-app | head -n 1)
    if [[ -z "$container_id" ]]; then
        log_error "Cannot find iva-app container"
        return 1
    fi
    service_name=$(docker inspect --format='{{index .Config.Labels "com.docker.compose.service"}}' "$container_id" 2>/dev/null || echo "")
    aliases=$(docker inspect --format='{{json .NetworkSettings.Networks.edge.Aliases}}' "$container_id" 2>/dev/null || echo "null")
    log "Container aliases on edge: $aliases (service: $service_name)"
    if echo "$aliases" | grep -qE '"app"'; then
        log_error "FATAL: Container has generic alias 'app' on edge network!"
        log_error "This collides with other services. The service must be named 'iva', not 'app'."
        return 1
    fi
    log "Network alias check passed (no generic 'app' alias)"
    return 0
}

health_check() {
    local start_time elapsed
    start_time=$(date +%s)
    log "Starting health check (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."
    while true; do
        elapsed=$(( $(date +%s) - start_time ))
        if (( elapsed >= HEALTH_CHECK_TIMEOUT )); then
            log_error "Health check timed out after ${HEALTH_CHECK_TIMEOUT}s"
            return 1
        fi
        local container_health
        container_health=$(get_container_health)
        if [[ "$container_health" == "healthy" ]]; then
            if curl -sf --resolve "${HEALTH_CHECK_HOST}:443:127.0.0.1" \
                    "https://${HEALTH_CHECK_HOST}/api/health" > /dev/null 2>&1; then
                log "Health check passed (container: healthy, API: responding)"
                return 0
            fi
        fi
        log "Health check pending (container: ${container_health}, elapsed: ${elapsed}s)..."
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

deploy_tag() {
    local tag="$1"
    local commit="${2:-}"
    if [[ -z "$commit" ]]; then
        commit="${tag#sha-}"
    fi
    log "Deploying tag: $tag (commit: $commit)"
    cd "$REPO_DIR"
    if ! git checkout --detach "$commit" 2>/dev/null; then
        log_error "Cannot checkout commit: $commit"
        return 1
    fi
    log "Checked out commit: $(git rev-parse HEAD)"
    "$VENV_PYTHON" scripts/deploy.py up -d --tag "$tag"
}

rollback() {
    local previous_tag="$1"
    local previous_commit="$2"
    log "Attempting rollback to tag: $previous_tag, commit: $previous_commit"
    cd "$REPO_DIR"
    if ! git checkout --detach "$previous_commit" 2>/dev/null; then
        log_error "Cannot checkout commit: $previous_commit"
        return 1
    fi
    "$VENV_PYTHON" scripts/deploy.py up -d --tag "$previous_tag"
}

do_deploy() {
    local tag="${SSH_ORIGINAL_COMMAND:-}"
    if [[ -z "$tag" ]]; then
        log_error "No command provided (SSH_ORIGINAL_COMMAND is empty)"
        exit 1
    fi
    validate_tag "$tag"
    local sha="${tag#sha-}"

    if [[ -f "$DEPLOY_ENV" ]]; then
        # shellcheck source=/dev/null
        source "$DEPLOY_ENV"
        export OCI_VAULT_OCID OCI_COMPARTMENT_ID
        if [[ -n "${IVA_VENV_PYTHON:-}" ]]; then
            VENV_PYTHON="$IVA_VENV_PYTHON"
        fi
    else
        log_error "Deploy environment file not found: $DEPLOY_ENV"
        exit 1
    fi

    cd "$REPO_DIR"
    log "Fetching origin/main..."
    git fetch origin main

    local full_sha
    full_sha=$(git rev-parse "$sha" 2>/dev/null || echo "")
    if [[ -z "$full_sha" ]]; then
        log_error "Cannot resolve commit: $sha"
        exit 1
    fi
    if ! git merge-base --is-ancestor "$full_sha" origin/main; then
        log_error "Commit $sha is not an ancestor of origin/main"
        log_error "Only commits on the main branch can be deployed"
        exit 1
    fi
    log "Verified commit $sha is on main branch"

    local previous_tag previous_commit
    previous_tag=$(get_current_tag)
    previous_commit=$(git rev-parse HEAD 2>/dev/null || echo "")

    log "=========================================="
    log "Starting deployment"
    log "New tag: $tag"
    log "Previous tag: ${previous_tag:-none}"
    log "Previous commit: ${previous_commit:-none}"
    log "=========================================="

    if ! deploy_tag "$tag" "$full_sha"; then
        log_error "Deployment failed"
        if [[ -n "$previous_tag" && -n "$previous_commit" ]]; then
            rollback "$previous_tag" "$previous_commit" || log_error "Rollback also failed."
        fi
        exit 1
    fi

    if ! check_network_aliases; then
        log_error "Network alias safety check failed"
        if [[ -n "$previous_tag" && -n "$previous_commit" ]]; then
            if rollback "$previous_tag" "$previous_commit"; then
                log "Rollback successful after alias check failure"
            else
                log_error "Rollback also failed."
            fi
        fi
        exit 1
    fi

    if ! health_check; then
        log_error "Health check failed for tag: $tag"
        if [[ -n "$previous_tag" && -n "$previous_commit" ]]; then
            if rollback "$previous_tag" "$previous_commit" && health_check; then
                log "Rollback successful, previous version is healthy"
            else
                log_error "Rollback failed or unhealthy. Manual intervention required."
            fi
        fi
        exit 1
    fi

    log "=========================================="
    log "Deployment successful: $tag"
    log "=========================================="
}

main() {
    local lock_dir
    lock_dir=$(dirname "$DEPLOY_LOCK")
    if [[ ! -d "$lock_dir" ]]; then
        mkdir -p "$lock_dir" 2>/dev/null || true
    fi
    exec 200>"$DEPLOY_LOCK"
    if ! flock -n 200; then
        log_error "Another IVA deployment is in progress (lock: $DEPLOY_LOCK)"
        exit 1
    fi
    do_deploy
}

main "$@"
