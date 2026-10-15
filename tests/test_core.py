import unittest
from unittest.mock import patch
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError

from before_report import ScanError, ground, model_compare, read_history, scan, validate_case, validate_history, validate_url


DRAFT = {
    "id": "DRAFT-1",
    "program": "A",
    "title": "Revoked preview still works",
    "summary": "A former viewer can load a private PDF after revocation.",
    "root_cause": "The preview handler ignores current share state.",
}
PRIOR = {
    "id": "OLD-1",
    "program": "A",
    "title": "Revoked share survives",
    "summary": "A copied token loads a private PDF after revocation.",
    "root_cause": "The preview handler ignores current share state.",
}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.draft = validate_case(DRAFT, "draft")
        self.prior = validate_case(PRIOR, "prior")

    def test_exact_quotes_are_required(self):
        answer = {
            "decision": "repeat",
            "draft_quote": "made-up evidence",
            "prior_quote": "The preview handler ignores current share state.",
            "explanation": "The root causes match.",
        }
        self.assertEqual(ground(answer, self.draft, self.prior)["decision"], "needs_review")

    def test_grounded_repeat(self):
        answer = {
            "decision": "repeat",
            "draft_quote": "The preview handler ignores current share state.",
            "prior_quote": "The preview handler ignores current share state.",
            "explanation": "The root causes match.",
        }
        self.assertEqual(ground(answer, self.draft, self.prior)["decision"], "repeat")

    def test_title_and_program_are_not_evidence(self):
        answer = {
            "decision": "distinct",
            "draft_quote": "Revoked preview still works",
            "prior_quote": "Revoked share survives",
            "explanation": "Different titles.",
        }
        self.assertEqual(ground(answer, self.draft, self.prior)["decision"], "needs_review")

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ScanError):
            validate_history([PRIOR, PRIOR])

    def test_csv_history_import(self):
        example = Path(__file__).resolve().parents[1] / "examples" / "history.csv"
        history = read_history(example)
        self.assertEqual([case["id"] for case in history], ["CASE-014", "CASE-021", "CASE-032"])
        self.assertEqual(history[0]["program_id"], "northstar-files")

    def test_external_endpoint_rejected(self):
        for endpoint in (
            "https://api.example.com/v1/chat/completions",
            "http://127.0.0.1.evil.test/v1/chat/completions",
            "http://127.0.0.1:8080/not-chat",
        ):
            with self.subTest(endpoint=endpoint), self.assertRaises(ScanError):
                validate_url(endpoint)

    def test_local_server_redirect_is_not_followed(self):
        hits = []

        class Destination(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append("followed")
                self.send_response(200)
                self.end_headers()

            def log_message(self, *_args):
                pass

        destination = ThreadingHTTPServer(("127.0.0.1", 0), Destination)

        class Redirect(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{destination.server_port}/v1/chat/completions")
                self.end_headers()

            def log_message(self, *_args):
                pass

        source = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        threads = [Thread(target=server.serve_forever, daemon=True) for server in (source, destination)]
        for thread in threads:
            thread.start()
        try:
            with self.assertRaises(HTTPError):
                model_compare(f"http://127.0.0.1:{source.server_port}/v1/chat/completions", "mock", self.draft, self.prior)
            self.assertEqual(hits, [])
        finally:
            for server in (source, destination):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_program_alias_cannot_greenlight_zero_comparisons(self):
        aliased = dict(self.draft, program="Totally Different Program")
        result = scan([self.prior], aliased, "http://127.0.0.1:1/v1/chat/completions", "offline")
        self.assertEqual(result["compared"], 0)
        self.assertEqual(result["verdict"], "review_needed")

    def test_legal_suffix_alias_is_compared_in_mixed_history(self):
        alias_prior = validate_case(dict(PRIOR, program="A, Inc."), "alias_prior")
        unrelated = validate_case(dict(PRIOR, id="OLD-2", summary="An unrelated page has escaped markup.", root_cause="HTML escaping at the template prevents injection."), "unrelated")

        def answer(_url, _model, _draft, prior):
            if prior["id"] == "OLD-1":
                return {
                    "decision": "repeat",
                    "draft_quote": "The preview handler ignores current share state.",
                    "prior_quote": "The preview handler ignores current share state.",
                    "explanation": "The same share-state check is absent.",
                }
            return {
                "decision": "distinct",
                "draft_quote": "The preview handler ignores current share state.",
                "prior_quote": "HTML escaping at the template prevents injection.",
                "explanation": "Different operation and missing check.",
            }

        with patch("before_report.model_compare", side_effect=answer):
            result = scan([alias_prior, unrelated], self.draft, "http://127.0.0.1:1/v1/chat/completions", "mock")
        self.assertEqual(result["verdict"], "likely_repeat")
        self.assertEqual(result["compared"], 2)

    def test_model_error_is_inconclusive(self):
        result = scan([self.prior], self.draft, "http://127.0.0.1:1/v1/chat/completions", "offline")
        self.assertEqual(result["verdict"], "review_needed")


if __name__ == "__main__":
    unittest.main()
