"""Build the Lambda bundle in build/lambda/, ready for `sam deploy` (no `sam build` step).

Why not `sam build`: on Windows it installs Windows wheels, and Pillow built for Windows fails to
import in Lambda. This script asks pip for Linux x86_64 wheels for Python 3.13 explicitly.

Bundle layout (zine/paths.py finds templates/ and static/ next to the package):
    build/lambda/zine/        the package, without dev-only modules
    build/lambda/templates/
    build/lambda/static/
    build/lambda/<jinja2, markupsafe, pillow, tzdata>   (boto3 comes from the Lambda runtime)

Run from the repo root:  python tools/build_lambda.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "lambda"
DEV_ONLY = {"dev_render_block1.py", "dev_render_golden.py", "dev_render_live.py", "dry_run.py",
            "fixture_feed.py", "publish_golden.py"}
DEPS = ["jinja2>=3.1", "pillow>=12.0", "tzdata"]


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "zine").mkdir(parents=True)
    for p in (ROOT / "src" / "zine").iterdir():
        if p.suffix in (".py", ".json") and p.name not in DEV_ONLY:
            shutil.copy2(p, OUT / "zine" / p.name)
    shutil.copytree(ROOT / "templates", OUT / "templates")
    shutil.copytree(ROOT / "static", OUT / "static")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--target", str(OUT),
                           "--platform", "manylinux2014_x86_64", "--implementation", "cp",
                           "--python-version", "3.13", "--only-binary=:all:", *DEPS])
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print("build/lambda ready: %.1f MB (Lambda limit 250 MB unzipped)" % (size / 1e6))


if __name__ == "__main__":
    main()
