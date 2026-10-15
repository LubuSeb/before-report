# BeforeReport

An offline second look before a researcher submits a paid security report. It compares a draft with the researcher's own prior cases and asks a local open-weight model whether the **root cause**, not just the title or product name, has already been submitted. It returns exact quoted evidence from both records and abstains when it cannot ground a judgment.

This project was started for the October 12–18, 2026 Hacktoberfest open-source AI challenge. It is a research aid, not a guarantee that a program has not seen the issue from someone else. It reads only the local files you specify and connects only to a loopback model server. No report data is sent to an external API.

## Quick start

Run an OpenAI-compatible local chat server such as `llama-server` with a Gemma 3 4B instruct GGUF. Then run:

```sh
python before_report.py scan --history examples/history.json --draft examples/draft.json --model gemma3 --url http://127.0.0.1:8080/v1/chat/completions
```

The example data is entirely synthetic. `--output result.json` writes the same JSON displayed to stdout. `--top-k` changes how many prior cases are adjudicated; a small setting can miss a semantically distant duplicate, so the default compares every case in a small history. The scan refuses non-loopback URLs. Exit code `2` means a likely repeat, `3` means an inconclusive result or model error, and `0` means no repeat was identified among the compared cases. None is a statement about the program's private duplicate inventory.

The draft is a JSON object. History can be a JSON array or a CSV exported from a spreadsheet. Each case has `id`, `program`, `title`, `summary`, and `root_cause`; `status`, `url`, and a stable `program_id` are optional. The included CSV is synthetic. For a renamed program, use the same `program_id` in old and new records. Do not publish your real private reports or the tool's output without reviewing their disclosure terms. The default output includes short excerpts to make its reasoning inspectable.

## Design

Keyword similarity can find obvious repeats but is brittle when two titles describe different symptoms of the same bug. BeforeReport orders candidates with local token overlap, then sends the draft and each prior case to the open-weight model for a pairwise root-cause comparison. The model must return exact, verbatim excerpts from both inputs. The program downgrades a claim to `needs_review` if either excerpt cannot be found in the supplied records; it never converts an ungrounded model answer into a safe-to-submit declaration. Even a `distinct` result is an aid to human review, not proof of novelty.

The current version is intended for individual researchers with tens of cases, not large public bug databases. Large files, external model endpoints, redirects, and unexpected response formats are rejected. The model can still make semantic mistakes despite valid quotes; its prose is explicitly labeled unverified. A different spelling or renamed program may require a shared `program_id` in both records. The included benchmark is a small synthetic smoke test, not an accuracy claim about real bounty reports.

## License

MIT for the code. Gemma model weights have separate terms from Google; obtain them from an official provider and follow those terms.
