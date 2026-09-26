"""voice_client.py . the one place that calls the model (task 3.2). Bedrock Runtime Converse.

It sends exactly what voices.py built (system prompt, and the user message with the edition and
the facts sheet) and returns the parsed JSON object, or None. voice_run.py does everything else:
schema, fact lock, banned words, retry, drop.

Never logs the prompt, the facts, or the model's text. Exceptions propagate; voice_run catches
them and logs only the exception type.

MODEL_ID: in the deployed stack, the ARN of the tagged application inference profile
`fcp-recap` (tech.md). For a local dev run, the system-defined profile
us.anthropic.claude-haiku-4-5-20251001-v1:0 works (confirmed in Block 0, LEDGER).
"""
import json
import os

TEMPERATURE = 0.8
MAX_TOKENS = 800  # design.md said ~600; a full 900-character recap plus the other fields needs headroom

_client = None


def _bedrock():
    global _client
    if _client is None:
        import boto3  # imported here so tests and offline renders never need AWS
        _client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return _client


def parse(text):
    """The first JSON object in the reply, or None. Tolerates a ```json fence around it."""
    if not isinstance(text, str):
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        out = json.loads(text[start:end + 1])
    except ValueError:
        return None
    return out if isinstance(out, dict) else None


def write(system, messages, client=None):
    """voice_run's `write`: (system prompt, Converse messages) -> dict or None."""
    resp = (client or _bedrock()).converse(
        modelId=os.environ["MODEL_ID"],
        system=[{"text": system}],
        messages=messages,
        inferenceConfig={"temperature": TEMPERATURE, "maxTokens": MAX_TOKENS},
    )
    content = resp.get("output", {}).get("message", {}).get("content", [])
    return parse("".join(c.get("text", "") for c in content))
