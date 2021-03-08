#!/bin/bash

# Export APPRUN if running from an extracted image
self="$(readlink -f -- $0)"
here="${self%/*}"
APPDIR="${APPDIR:-${here}}"

# Export SSL certificate
export SSL_CERT_FILE="${APPDIR}/opt/_internal/certs.pem"
export PYTHONHOME="${APPDIR}/opt/python3.9"

exec $APPDIR/usr/bin/runekit $@
