#!/bin/bash
set -e

# Start cron
crond

# Start MySQL
exec gosu mysql "$@"