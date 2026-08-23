#!/usr/bin/env bash
# Install aw-watcher-mic as a systemd user service.
set -euo pipefail

UNIT_NAME="aw-watcher-mic.service"
REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_TEMPLATE="${REPO_DIR}/misc/${UNIT_NAME}"
UNIT_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
UNIT_PATH="${UNIT_DIR}/${UNIT_NAME}"

PREFIX="${PREFIX:-${HOME}/.local}"
LIB_DIR="${PREFIX}/lib/aw-watcher-mic"
BIN_LINK="${PREFIX}/bin/aw-watcher-mic"

usage() {
    cat <<USAGE
Usage: ${0##*/} [--bundle | --uninstall]

Installs aw-watcher-mic as a systemd user service, started with the graphical
session and after aw-server.

  (no option)  point the service at the best executable already available
  --bundle     deploy dist/aw-watcher-mic (from 'make package') to
               ${PREFIX} first, so the service does not depend on the
               source checkout, then install the service
  --uninstall  stop and remove the service and any deployed bundle

Override the deployment location with PREFIX, for example:
  PREFIX=/opt/activitywatch ${0##*/} --bundle
USAGE
}

find_executable() {
    local venv
    if [ -x "${LIB_DIR}/aw-watcher-mic" ]; then
        printf '%s\n' "${LIB_DIR}/aw-watcher-mic"
        return 0
    fi
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

deploy_bundle() {
    local built="${REPO_DIR}/dist/aw-watcher-mic"
    if [ ! -x "${built}/aw-watcher-mic" ]; then
        echo "error: no bundle at ${built}; run 'make package' first" >&2
        return 1
    fi

    rm -rf "${LIB_DIR}"
    mkdir -p "${LIB_DIR}" "$(dirname -- "${BIN_LINK}")"
    cp -a "${built}/." "${LIB_DIR}/"
    ln -sfn "${LIB_DIR}/aw-watcher-mic" "${BIN_LINK}"

    echo "Deployed ${LIB_DIR}"
    echo "Linked   ${BIN_LINK}"
}

uninstall() {
    if [ -f "${UNIT_PATH}" ]; then
        systemctl --user disable --now "${UNIT_NAME}"
        rm -f "${UNIT_PATH}"
        systemctl --user daemon-reload
        echo "Removed ${UNIT_PATH}"
    else
        echo "Not installed: ${UNIT_PATH}"
    fi

    if [ -L "${BIN_LINK}" ]; then
        rm -f "${BIN_LINK}"
        echo "Removed ${BIN_LINK}"
    fi
    if [ -d "${LIB_DIR}" ]; then
        rm -rf "${LIB_DIR}"
        echo "Removed ${LIB_DIR}"
    fi
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
    systemctl --user enable "${UNIT_NAME}"
    systemctl --user restart "${UNIT_NAME}"
    systemctl --user --no-pager status "${UNIT_NAME}" || true
}

case "${1:-}" in
    --bundle)
        deploy_bundle
        install_unit
        ;;
    --uninstall) uninstall ;;
    -h | --help) usage ;;
    "") install_unit ;;
    *)
        usage >&2
        exit 1
        ;;
esac
