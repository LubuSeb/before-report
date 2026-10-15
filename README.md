# BeforeReport

An offline second look before a researcher submits a paid security report. It compares a draft with the researcher's own prior cases and asks a local open-weight model whether the **root cause**, not just the title or product name, has already been submitted. It returns exact quoted evidence from both records and abstains when it cannot ground a judgment.

This project was started for the October 12–18, 2026 Hacktoberfest open-source AI challenge. It is a research aid, not a guarantee that a program has not seen the issue from someone else. It reads only the local files you specify and connects only to a loopback model server. Check that your local server runs a downloaded model rather than forwarding requests to a cloud provider.

## Quick start

Install [Ollama](https://ollama.com/download), pull the local model, and run the scan:

```sh
ollama pull gemma3:4b
python before_report.py scan --history examples/history.csv --draft examples/draft.json --model gemma3:4b --url http://127.0.0.1:11434/v1/chat/completions
```

Alternatively, run an OpenAI-compatible local server such as `llama-server` with a Gemma 3 4B instruct GGUF, then run:

```sh
python before_report.py scan --history examples/history.json --draft examples/draft.json --model gemma3 --url http://127.0.0.1:8080/v1/chat/completions
```

The example data is entirely synthetic. `--output result.json` writes the same JSON displayed to stdout. `--top-k` changes how many prior cases are adjudicated; a small setting can miss a semantically distant duplicate, so the default compares every same-program case in a small history. The scan refuses non-loopback URLs. Exit code `2` means a likely repeat, `3` means an inconclusive result or model error, and `0` means no repeat was identified among the compared cases. None is a statement about the program's private duplicate inventory.

[Watch the 27-second demo replay](demo/before-report-demo.mp4), rendered from an actual local scan of the synthetic files. The [unedited CLI transcript](demo/live-scan.txt) separately records a fresh Gemma invocation, command, timing, exit code, and full output. Run `python demo/capture_run.py --url http://127.0.0.1:8080/v1/chat/completions --model gemma3` to capture your own run. `demo/render.py` regenerates the visual replay from `result.json` after `pip install pillow`; `ffmpeg` is required for rendering only.

The draft is a JSON object. History can be a JSON array or a CSV exported from a spreadsheet. Each case has `id`, `program`, `title`, `summary`, and `root_cause`; `status`, `url`, and a stable `program_id` are optional. The included CSV is synthetic. For a renamed program, use the same `program_id` in old and new records. Do not publish your real private reports or the tool's output without reviewing their disclosure terms. The default output includes short excerpts to make its reasoning inspectable.

## Design

Keyword similarity can find obvious repeats but is brittle when two titles describe different symptoms of the same bug. BeforeReport orders candidates with local token overlap, then sends the draft and each prior case to the open-weight model for a pairwise root-cause comparison. The model must return exact, verbatim excerpts from both inputs. The program downgrades a claim to `needs_review` if either excerpt cannot be found in the supplied records; it never converts an ungrounded model answer into a safe-to-submit declaration. Even a `distinct` result is an aid to human review, not proof of novelty.

The current version is intended for individual researchers with tens of cases, not large public bug databases. Large files, external model endpoints, redirects, and unexpected response formats are rejected. The model can still make semantic mistakes despite valid quotes; its prose is explicitly labeled unverified. A different spelling or renamed program may require a shared `program_id` in both records. The included benchmark is a small synthetic smoke test, not an accuracy claim about real bounty reports.

## What the test showed

Run `python -m unittest discover -s tests -v` for input, privacy-boundary and fail-closed tests. For a model smoke test, run `python benchmarks/run.py --url http://127.0.0.1:11434/v1/chat/completions --model gemma3:4b`. The [recorded local Gemma 3 4B run](benchmarks/gemma3-4b-results.json) used `llama-server` build 11669 and a model file with SHA-256 `f06e91e18fc74295d0c781bf91622508c75655e2c18ed869d52447ffe1e667e1`.

On fifteen hand-written synthetic pairs, the complete cautious/not-cautious workflow matched fourteen labels, with **no false clearance** and **one false alarm** caused by an instruction embedded in a prior case. Fourteen pairs invoked the model; the other was a deliberate cross-program hold. A fixed program-aware token-overlap baseline (score at least 0.7) matched eleven labels. The last seven cases were added after the prompt and cutoff were set: the model workflow matched seven, the lexical baseline four. These small invented cases do not establish a field accuracy rate. A green result still needs human duplicate and program-scope review.

## License

MIT for the code. Gemma model weights have separate terms from Google; obtain them from an official provider and follow those terms.
