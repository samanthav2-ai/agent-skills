#!/bin/bash
# clawdbot-watchdog.sh — Health-check watchdog for Clawdbot Gateway
#
# SOLE RESPONSIBILITY: Verify the gateway is actually healthy (WebSocket
# accepting connections, WhatsApp listening). If unhealthy, restart via
# systemd. Never compete with systemd — always use systemctl.
#
# Checks:
#   1. systemd service is active
#   2. Gateway WebSocket port is listening
#   3. HTTP health probe responds (not just process alive)
#   4. Only one gateway process running (no duplicates)
#
# If unhealthy for UNHEALTHY_THRESHOLD seconds, force restart.

OWNER_JID="${CLAWDBOT_SOS_TARGET:-14156236154@s.whatsapp.net}"
CHECK_INTERVAL=10
UNHEALTHY_THRESHOLD=30
GATEWAY_PORT=18789
CLAWDBOT_STATE_DIR="${CLAWDBOT_STATE_DIR:-/home/ubuntu/.clawdbot}"
WACLI_STORE="${WACLI_STORE:-/home/ubuntu/.wacli}"

unhealthy_seconds=0
last_state="unknown"
sos_sent="false"
consecutive_restarts=0
MAX_CONSECUTIVE_RESTARTS=5
RESTART_COOLDOWN=120

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WATCHDOG: $1"
}

send_sos() {
    local message="$1"
    log "SOS: $message"

    local sos_file="${CLAWDBOT_STATE_DIR}/pending-sos.txt"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$sos_file"

    if command -v wacli &> /dev/null; then
        wacli send text --to "$OWNER_JID" --message "[JARED SOS] $message" \
            --store "$WACLI_STORE" --timeout 10s 2>/dev/null || true
    fi
}

check_health() {
    # 1. Is the systemd service active?
    if ! systemctl is-active --quiet clawdbot 2>/dev/null; then
        echo "dead"
        return
    fi

    # 2. Is the gateway port listening?
    if ! ss -tlnp 2>/dev/null | grep -q ":${GATEWAY_PORT} "; then
        echo "unhealthy"
        return
    fi

    # 3. Can we get an HTTP response?
    local http_status
    http_status=$(curl -s -o /dev/null -w '%{http_code}' \
        --connect-timeout 3 --max-time 5 \
        "http://127.0.0.1:${GATEWAY_PORT}/" 2>/dev/null) || http_status="000"

    if [ "$http_status" = "000" ]; then
        echo "unhealthy"
        return
    fi

    # 4. Verify exactly one process holds the port (catch duplicates)
    local port_pids
    port_pids=$(fuser ${GATEWAY_PORT}/tcp 2>/dev/null | wc -w) || port_pids=0

    if [ "$port_pids" -gt 2 ]; then
        # More than parent+child holding the port — something is wrong
        log "WARNING: $port_pids PIDs on port $GATEWAY_PORT — restarting"
        sudo systemctl restart clawdbot 2>/dev/null
        echo "unhealthy"
        return
    fi

    echo "healthy"
}

do_restart() {
    log "Restarting gateway via systemctl..."
    consecutive_restarts=$((consecutive_restarts + 1))

    if [ "$consecutive_restarts" -ge "$MAX_CONSECUTIVE_RESTARTS" ]; then
        send_sos "CRITICAL: Gateway restarted $consecutive_restarts times. Cooling down ${RESTART_COOLDOWN}s."
        log "Restart limit hit. Cooling down..."
        sleep "$RESTART_COOLDOWN"
        consecutive_restarts=0
    fi

    sudo systemctl restart clawdbot 2>/dev/null
    sleep 8

    local post_state
    post_state=$(check_health)

    if [ "$post_state" = "healthy" ]; then
        log "Gateway recovered"
        send_sos "Gateway recovered after restart."
        # No separate recovery agent — AGENTS.md tells Jared to read
        # ACTIVE_WORK.md on every session start, so the next inbound
        # message will naturally resume any in-progress work.
        return 0
    else
        log "Gateway still unhealthy after restart (state: $post_state)"
        return 1
    fi
}

main() {
    log "Started — port=$GATEWAY_PORT interval=${CHECK_INTERVAL}s threshold=${UNHEALTHY_THRESHOLD}s"

    while true; do
        local state
        state=$(check_health)

        case "$state" in
            healthy)
                if [ "$last_state" != "healthy" ]; then
                    log "Gateway healthy"
                fi
                unhealthy_seconds=0
                consecutive_restarts=0
                ;;

            dead)
                unhealthy_seconds=$((unhealthy_seconds + CHECK_INTERVAL))
                log "Gateway DEAD (systemd inactive) — ${unhealthy_seconds}s"

                if [ "$last_state" = "healthy" ]; then
                    send_sos "Gateway died. Auto-restarting in ${UNHEALTHY_THRESHOLD}s."
                    sos_sent="true"
                fi

                if [ "$unhealthy_seconds" -ge "$UNHEALTHY_THRESHOLD" ]; then
                    do_restart
                    unhealthy_seconds=0
                fi
                ;;

            unhealthy)
                unhealthy_seconds=$((unhealthy_seconds + CHECK_INTERVAL))
                log "Gateway UNHEALTHY (process alive, not responding) — ${unhealthy_seconds}s"

                if [ "$last_state" = "healthy" ] && [ "$sos_sent" = "false" ]; then
                    send_sos "Gateway unhealthy (alive but not responding). Watching..."
                    sos_sent="true"
                fi

                if [ "$unhealthy_seconds" -ge "$UNHEALTHY_THRESHOLD" ]; then
                    log "Unhealthy threshold reached — forcing restart"
                    do_restart
                    unhealthy_seconds=0
                fi
                ;;
        esac

        last_state="$state"
        if [ "$state" = "healthy" ]; then
            sos_sent="false"
        fi

        sleep "$CHECK_INTERVAL"
    done
}

trap 'log "Stopping"; exit 0' SIGTERM SIGINT

main
