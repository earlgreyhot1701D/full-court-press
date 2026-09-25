"""The BALLDONTLIE API key. Task 2.2.

Named api_key.py, not secrets.py as structure.md first said: a module called `secrets` shadows
Python's standard library module of that name and breaks anything that imports it, in ways that
are hard to trace. Recorded in LEDGER.

Order: the BDL_API_KEY environment variable (local dev, set for one process by
tools/fetch_golden.ps1), else SSM Parameter Store SecureString at BDL_KEY_PARAM (Lambda).
Held in memory for the life of the process. Never logged, printed, returned in an error, or
written anywhere.
"""
import os

DEFAULT_PARAM = "/full-court-press/bdl-api-key"
_cached = None


class KeyUnavailable(Exception):
    """Raised with a message that never contains the key."""


def get_key(ssm_client=None):
    global _cached
    if _cached:
        return _cached
    env = os.environ.get("BDL_API_KEY", "").strip()
    if env:
        _cached = env
        return _cached
    name = os.environ.get("BDL_KEY_PARAM", DEFAULT_PARAM)
    try:
        if ssm_client is None:
            import boto3                                   # provided by the Lambda runtime
            ssm_client = boto3.client("ssm")
        value = ssm_client.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"].strip()
    except Exception as e:                                 # never include the response or value
        raise KeyUnavailable("could not read %s: %s" % (name, type(e).__name__)) from None
    if not value:
        raise KeyUnavailable("parameter %s is empty" % name)
    _cached = value
    return _cached


def _reset_for_tests():
    global _cached
    _cached = None
