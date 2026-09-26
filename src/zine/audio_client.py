"""Amazon Polly, neural engine only (Req 16.2, 16.5). Returns MP3 bytes or None. Never logs the text.

Why neural: Polly's generative engine can produce speech not in the script, and its safeguard
"does not provide complete protection" (Polly docs). Neural reads exactly the text it is given.
"""
import os

ENGINE = "neural"


def speak(text, client=None):
    if os.environ.get("POLLY_ENGINE", ENGINE) != ENGINE:
        raise ValueError("only the neural engine is allowed")  # never generative
    if client is None:
        import boto3
        client = boto3.client("polly", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    try:
        resp = client.synthesize_speech(Engine=ENGINE, VoiceId=os.environ.get("POLLY_VOICE", "Danielle"),
                                        OutputFormat="mp3", Text=text, TextType="text")
        return resp["AudioStream"].read()
    except Exception:
        return None
