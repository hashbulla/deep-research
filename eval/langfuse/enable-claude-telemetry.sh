#!/usr/bin/env bash
# SOURCE this (do not execute) to enable Claude Code OTEL export to the local Collector,
# then launch a traced session in the SAME shell:
#
#     source eval/langfuse/enable-claude-telemetry.sh && claude
#
# Telemetry is best-effort: if the Collector is down, the run still proceeds (fail-open).
# Content is OFF by default in Claude Code; the opt-in flags below turn it on, and the
# Collector redacts it before egress. Comment them out for metadata-only tracing.

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1      # REQUIRED for trace spans — without it, 0 spans emit (verified 2026-06-25, 2.1.191)
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp                  # traces are beta in Claude Code (CLI-only); gated by the BETA flag above
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf  # protobuf dodges the OTLP/JSON int64 usage-drop bug
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_METRIC_EXPORT_INTERVAL=10000          # 10s, for faster feedback during verification
export OTEL_LOGS_EXPORT_INTERVAL=5000

# Content opt-in (highest signal, redacted at the Collector). Drop these for metadata-only.
export OTEL_LOG_USER_PROMPTS=1
export OTEL_LOG_TOOL_DETAILS=1
export OTEL_LOG_TOOL_CONTENT=1
# export OTEL_LOG_RAW_API_BODIES=1   # raw Messages API bodies deliberately OFF under reduce-surface posture; completion text comes from assistant_response log event instead

# Identify the run in Langfuse (Session grouping is by session.id).
export OTEL_RESOURCE_ATTRIBUTES="service.name=deep-research,service.version=skill,deployment.environment=local,session.id=${LANGFUSE_SESSION_ID:-deep-research-$$}"

echo "Claude Code OTEL ENABLED -> http://localhost:4318  (service.name=deep-research, session.id=${LANGFUSE_SESSION_ID:-deep-research-$$})"
echo "Content flags: USER_PROMPTS=$OTEL_LOG_USER_PROMPTS TOOL_CONTENT=$OTEL_LOG_TOOL_CONTENT (redacted at the Collector)"
echo "Now launch the traced session in THIS shell:  claude"
