#!/usr/bin/env bash
# Install aw-watcher-mic as a systemd user service.
set -euo pipefail

UNIT_NAME="aw-watcher-mic.service"
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_TEMPLATE="${REPO_DIR}/misc/${UNIT_NAME}"
UNIT_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
UNIT_PATH="${UNIT_DIR}/${UNIT_NAME}"

usage() {
    cat <<USAGE
Usage: ${0##*/} [--uninstall]

Installs aw-watcher-mic as a systemd user service, started with the graphical
session and after aw-server. With --uninstall, stops and removes it.
USAGE
}

find_executable() {
    local venv
    if venv="$(cd -- "${REPO_DIR}" && poetry env info --path 2>/dev/null)" &&
        [ -x "${venv}/bin/aw-watcher-mic" ]; then
        printf '%s\n' "${venv}/bin/aw-watcher-mic"
        return 0
    fi
    if [ -x "${REPO_DIR}/.venv/bin/aw-watcher-mic" ]; then
        printf '%s\n' "${REPO_DIR}/.venv/bin/aw-watcher-mic"
        return 0
    fi
    command -v aw-watcher-mic 2>/dev/null
}

uninstall() {
    if [ ! -f "${UNIT_PATH}" ]; then
        echo "Not installed: ${UNIT_PATH}"
        return 0
    fi
    systemctl --user disable --now "${UNIT_NAME}"
    rm -f "${UNIT_PATH}"
    systemctl --user daemon-reload
    echo "Removed ${UNIT_PATH}"
}

install_unit() {
    local exec_start
    if ! exec_start="$(find_executable)" || [ -z "${exec_start}" ]; then
        echo "error: no aw-watcher-mic executable found; run 'make install' first" >&2
        return 1
    fi
    if [ ! -f "${UNIT_TEMPLATE}" ]; then
        echo "error: missing unit template ${UNIT_TEMPLATE}" >&2
        return 1
    fi

    mkdir -p "${UNIT_DIR}"
    sed "s|__EXEC_START__|${exec_start}|" "${UNIT_TEMPLATE}" >"${UNIT_PATH}"
    echo "Wrote ${UNIT_PATH}"
    echo "ExecStart=${exec_start}"

    systemctl --user daemon-reload
    systemctl --user enable --now "${UNIT_NAME}"
    systemctl --user --no-pager status "${UNIT_NAME}" || true
}

case "${1:-}" in
    --uninstall) uninstall ;;
    -h | --help) usage ;;
    "") install_unit ;;
    *)
        usage >&2
        exit 1
        ;;
esac
