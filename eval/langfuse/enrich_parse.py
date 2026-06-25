"""Parse the Collector's file-exported OTLP logs (JSONL) into flat LogRecords."""
import json
from dataclasses import dataclass

@dataclass
class LogRecord:
    trace_id: str
    span_id: str
    event_name: str
    attrs: dict

def _attr_value(v: dict):
    for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if k in v:
            return int(v[k]) if k == "intValue" else v[k]
    return None

def _flatten_attrs(attr_list):
    out = {}
    for a in attr_list or []:
        out[a["key"]] = _attr_value(a.get("value", {}))
    return out

def parse_jsonl(path: str) -> list:
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            for rl in req.get("resourceLogs", []):
                for sl in rl.get("scopeLogs", []):
                    for lr in sl.get("logRecords", []):
                        attrs = _flatten_attrs(lr.get("attributes", []))
                        records.append(LogRecord(
                            trace_id=lr.get("traceId", ""),
                            span_id=lr.get("spanId", ""),
                            event_name=attrs.get("event.name", ""),
                            attrs=attrs,
                        ))
    return records
