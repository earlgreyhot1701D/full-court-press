"""One small interface over a local folder or an S3 bucket: put, get, exists, keys.

Keys are '/'-separated. The site lives under `site/`, private state under `state/` and `cache/`.
Only `site/` is behind CloudFront (the bucket policy and origin path in template.yaml).
"""
import os

SITE = "site/"


def cache_control(key):
    if key.endswith((".html", ".json")):
        return "public, max-age=300"          # pages and data change every morning
    if "/static/" in "/" + key:
        return "public, max-age=3600"         # CSS/JS/fonts change only on deploy
    return "public, max-age=86400"            # cards and audio


class LocalStore:
    def __init__(self, root):
        self.root = root

    def _p(self, key):
        return os.path.join(self.root, *key.split("/"))

    def put(self, key, body, content_type=None):
        p = self._p(key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(body if isinstance(body, bytes) else body.encode("utf-8"))

    def get(self, key):
        try:
            with open(self._p(key), "rb") as fh:
                return fh.read()
        except FileNotFoundError:
            return None

    def exists(self, key):
        return os.path.exists(self._p(key))

    def keys(self, prefix):
        base = self._p(prefix.rstrip("/"))
        out = []
        for dirpath, _d, names in os.walk(base):
            for n in names:
                rel = os.path.relpath(os.path.join(dirpath, n), self.root).replace(os.sep, "/")
                out.append(rel)
        return sorted(out)


class S3Store:
    def __init__(self, bucket, client=None):
        self.bucket = bucket
        if client is None:
            import boto3
            client = boto3.client("s3")
        self.s3 = client

    def put(self, key, body, content_type=None):
        kw = {"Bucket": self.bucket, "Key": key, "Body": body if isinstance(body, bytes) else body.encode("utf-8"),
              "CacheControl": cache_control(key)}
        if content_type:
            kw["ContentType"] = content_type
        self.s3.put_object(**kw)

    def get(self, key):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None

    def exists(self, key):
        return self.get(key) is not None

    def keys(self, prefix):
        out, token = [], None
        while True:
            kw = {"Bucket": self.bucket, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            resp = self.s3.list_objects_v2(**kw)
            out += [o["Key"] for o in resp.get("Contents", [])]
            if not resp.get("IsTruncated"):
                return sorted(out)
            token = resp.get("NextContinuationToken")


def publish(store, files):
    """Write site files {site_path: (bytes, content_type)} under site/."""
    for path, (body, ctype) in sorted(files.items()):
        store.put(SITE + path, body, ctype)
    return len(files)
