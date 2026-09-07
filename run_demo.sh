#!/usr/bin/env sh
set -eu
python3 dist/DIKWP_MINEX_FABRIC_OS.pyz suite --root . --output outputs/demo
printf '\nOpen web/DIKWP_MINEX_FABRIC_OS_Dashboard.html in a browser.\n'
