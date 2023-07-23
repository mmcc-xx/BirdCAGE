#!/command/with-contenv bashio
# shellcheck shell=bash
# ==============================================================================
# Home Assistant Community Add-on: Example
#
# Example add-on for Home Assistant.
# ------------------------------------------------------------------------------
main() {
    bashio::log.trace "${FUNCNAME[0]}"

    while true; do
        echo "Second Script Output"
        sleep 10
    done
}
main "$@"
