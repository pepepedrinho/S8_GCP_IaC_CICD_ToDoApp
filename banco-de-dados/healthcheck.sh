#!/usr/bin/env bash
set -euo pipefail
# Initialization binds only loopback. The final daemon binds this address.
# Authenticated readiness is checked separately by the API's database ping.
address=$(hostname -i)
address=${address%% *}
exec 3<>"/dev/tcp/$address/27017"
exec 3>&-
