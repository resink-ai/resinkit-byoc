#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046,SC1090

set -eo pipefail


drop_privs_cmd() {
    if [ "$(id -u)" != 0 ]; then
        # Don't need to drop privs if EUID != 0
        return
    elif [ -x /sbin/su-exec ]; then
        # Alpine
        echo su-exec "resinkit"
    else
        # Others
        echo gosu "resinkit"
    fi
}

# Run entrypoint.sh with resinkit role
exec $(drop_privs_cmd) /home/resinkit/.local/bin/entrypoint.sh start
exec $(drop_privs_cmd) /home/resinkit/.local/bin/entrypoint.sh status
