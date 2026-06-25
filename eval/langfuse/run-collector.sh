#!/usr/bin/env bash
# Boot the AI-182 OTEL Collector egress gate (Claude Code -> Langfuse Cloud).
# Sources Langfuse creds from the second-brain secret store, composes the OTLP
# Basic-auth header, runs the *contrib* Collector in Docker.
#
# The secret key is NEVER printed, logged, or committed. Only its presence is checked
# and the composed header's length is shown.
#
# Usage:   ./run-collector.sh            # start (detached)
#          docker logs -f langfuse-otelcol   # watch
#          docker rm -f langfuse-otelcol     # stop
set -euo pipefail

SECRETS_FILE="${LANGFUSE_ENV_FILE:-$HOME/second-brain/.secrets/langfuse.env}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HERE/otel-collector-config.yaml"
IMAGE="${OTELCOL_IMAGE:-otel/opentelemetry-collector-contrib:0.155.0}"
CONTAINER="${OTELCOL_CONTAINER:-langfuse-otelcol}"

[ -f "$SECRETS_FILE" ] || { echo "FATAL: secrets file not found: $SECRETS_FILE" >&2; exit 1; }
[ -f "$CONFIG" ]       || { echo "FATAL: collector config not found: $CONFIG" >&2; exit 1; }

# Load creds — values stay in the env, never echoed.
set -a
# shellcheck disable=SC1090
source "$SECRETS_FILE"
set +a
: "${LANGFUSE_PUBLIC_KEY:?missing LANGFUSE_PUBLIC_KEY in $SECRETS_FILE}"
: "${LANGFUSE_SECRET_KEY:?missing LANGFUSE_SECRET_KEY in $SECRETS_FILE}"
: "${LANGFUSE_BASE_URL:?missing LANGFUSE_BASE_URL in $SECRETS_FILE}"

# Normalize base URL -> OTLP endpoint.
base="$LANGFUSE_BASE_URL"
[[ "$base" =~ ^https?:// ]] || base="https://$base"
base="${base%/}"
export LANGFUSE_OTLP_ENDPOINT="$base/api/public/otel"
export LANGFUSE_OTLP_AUTH="Basic $(printf '%s:%s' "$LANGFUSE_PUBLIC_KEY" "$LANGFUSE_SECRET_KEY" | base64 -w0)"

echo "Collector image:  $IMAGE"
echo "OTLP endpoint:    $LANGFUSE_OTLP_ENDPOINT"
echo "Auth header:      Basic <redacted, ${#LANGFUSE_OTLP_AUTH} chars>"
echo "Config:           $CONFIG"

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" \
  -p 4317:4317 -p 4318:4318 -p 8888:8888 \
  -e LANGFUSE_OTLP_ENDPOINT \
  -e LANGFUSE_OTLP_AUTH \
  -v "$CONFIG:/etc/otelcol-contrib/config.yaml:ro" \
  "$IMAGE" >/dev/null

echo "Started '$CONTAINER'. Receivers on :4317 (gRPC) / :4318 (HTTP). Tail: docker logs -f $CONTAINER"
