#!/bin/bash
# shellcheck disable=SC1091,SC2046

set -eo pipefail

# export UV_INSTALL_DIR=/opt/uv
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/opt/uv" sh

