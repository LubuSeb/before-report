"""Capture a genuine CLI/model run against the included synthetic examples.

Start a local OpenAI-compatible Gemma server first. The transcript records the
exact command, UTC timing, exit code, and unedited stdout/stderr. It contains no
private bounty material because only the repository's invented examples are read.
"""

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    command = [
        sys.executable, "before_report.py", "scan",
        "--history", "examples/history.csv",
        "--draft", "examples/draft.json",
        "--url", args.url,
        "--model", args.model,
    ]
    start = dt.datetime.now(dt.timezone.utc)
    tick = time.monotonic()
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    end = dt.datetime.now(dt.timezone.utc)
    elapsed = time.monotonic() - tick
    display = "python before_report.py scan --history examples/history.csv --draft examples/draft.json --url " + args.url + " --model " + args.model
    transcript = (
        "# Genuine BeforeReport CLI run against synthetic repository examples\n"
        f"# Start UTC: {start.isoformat()}\n"
        f"# End UTC: {end.isoformat()}\n"
        f"# Duration: {elapsed:.2f} seconds\n"
        f"$ {display}\n"
        f"# Exit code: {completed.returncode} (3 means review needed)\n"
        "# stdout follows unchanged\n"
        + completed.stdout
        + "# stderr follows unchanged\n"
        + completed.stderr
    )
    target = ROOT / "demo" / "live-scan.txt"
    target.write_text(transcript, encoding="utf-8")
    print(target)
    return 0 if completed.returncode == 3 and '"verdict": "review_needed"' in completed.stdout else 1


if __name__ == "__main__":
    raise SystemExit(main())
