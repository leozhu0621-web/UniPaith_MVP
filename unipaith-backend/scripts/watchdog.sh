#!/bin/bash
# UniPaith AI Engine Watchdog
# Runs every 5 minutes via cron. Checks health, auto-heals, and logs alerts.
#
# Install: sudo crontab -e
#   */5 * * * * /opt/app/scripts/watchdog.sh >> /var/log/unipaith-watchdog.log 2>&1

set -euo pipefail

HEALTH_URL="http://localhost:8000/api/v1/internal/health"
SERVICE_NAME="unipaith"
LOG_PREFIX="[WATCHDOG $(date -u '+%Y-%m-%d %H:%M:%S UTC')]"
MAX_RESTART_COUNT=3
RESTART_COUNT_FILE="/tmp/unipaith-restart-count"
ALERT_FILE="/tmp/unipaith-alert-sent"

# --- Helpers ---

log() { echo "$LOG_PREFIX $1"; }

reset_restart_counter() {
    echo "0" > "$RESTART_COUNT_FILE"
}

get_restart_count() {
    if [ -f "$RESTART_COUNT_FILE" ]; then
        cat "$RESTART_COUNT_FILE"
    else
        echo "0"
    fi
}

increment_restart_count() {
    local count
    count=$(get_restart_count)
    echo $((count + 1)) > "$RESTART_COUNT_FILE"
}

# --- Checks ---

# Check 1: Is the service running?
check_service() {
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log "CRITICAL: Service $SERVICE_NAME is not running!"
        return 1
    fi
    return 0
}

# Check 2: Can the API respond?
check_api() {
    local response
    response=$(curl -m 10 -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$response" = "000" ]; then
        log "CRITICAL: API not responding (connection failed)"
        return 1
    elif [ "$response" != "200" ]; then
        log "WARNING: API returned HTTP $response"
        return 1
    fi
    return 0
}

# Check 3: Is the health endpoint reporting healthy?
check_health_details() {
    local body
    body=$(curl -m 10 -s "$HEALTH_URL" 2>/dev/null || echo '{"status":"unreachable"}')
    local status
    status=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "parse_error")

    case "$status" in
        healthy)
            log "OK: Engine healthy"
            reset_restart_counter
            # Clear alert flag when healthy
            rm -f "$ALERT_FILE"
            return 0
            ;;
        degraded)
            log "WARNING: Engine degraded — $body"
            return 0  # Don't restart for degraded, just log
            ;;
        critical)
            log "CRITICAL: Engine critical — $body"
            return 1
            ;;
        *)
            log "ERROR: Unexpected health status: $status"
            return 1
            ;;
    esac
}

# Check 4: Memory usage
check_memory() {
    local mem_pct
    mem_pct=$(free | awk '/Mem/{printf("%.0f", $3/$2 * 100)}')
    if [ "$mem_pct" -gt 90 ]; then
        log "WARNING: Memory usage at ${mem_pct}%"
        return 1
    fi
    return 0
}

# Check 5: Disk usage
check_disk() {
    local disk_pct
    disk_pct=$(df / | awk 'NR==2{print $5}' | tr -d '%')
    if [ "$disk_pct" -gt 90 ]; then
        log "WARNING: Disk usage at ${disk_pct}%"
        return 1
    fi
    return 0
}

# --- Recovery ---

attempt_restart() {
    local count
    count=$(get_restart_count)

    if [ "$count" -ge "$MAX_RESTART_COUNT" ]; then
        log "ALERT: Exceeded max restart attempts ($MAX_RESTART_COUNT). Manual intervention needed!"
        # Write alert file so admin dashboard picks it up
        echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')|Service exceeded max auto-restarts ($MAX_RESTART_COUNT). Check logs: journalctl -u $SERVICE_NAME" > /tmp/unipaith-alert.json
        return 1
    fi

    log "Attempting restart ($((count + 1))/$MAX_RESTART_COUNT)..."
    systemctl restart "$SERVICE_NAME"
    increment_restart_count
    sleep 10

    # Verify it came back
    if check_service && check_api; then
        log "Restart successful!"
        return 0
    else
        log "Restart failed — service still unhealthy"
        return 1
    fi
}

# --- Main ---

main() {
    local needs_restart=false

    # Service check
    if ! check_service; then
        needs_restart=true
    fi

    # API check (only if service is running)
    if [ "$needs_restart" = false ] && ! check_api; then
        needs_restart=true
    fi

    # Health details (only if API is responding)
    if [ "$needs_restart" = false ] && ! check_health_details; then
        needs_restart=true
    fi

    # Resource checks (always run)
    check_memory || true
    check_disk || true

    # Auto-heal if needed
    if [ "$needs_restart" = true ]; then
        attempt_restart
    fi
}

main
