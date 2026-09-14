"""Preserve the shared bot-merge safety gates while cleaning up its Python style."""

import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

POLICY_PATH = Path(__file__).resolve().parents[1] / ".github/scripts/checked-bot-merge.py"
SPEC = importlib.util.spec_from_file_location("merge_policy", POLICY_PATH)
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


class MergePolicyTests(unittest.TestCase):
    """Use synthetic metadata and intercept every possible GitHub operation."""

    def setUp(self):
        self.pr = {
            "state": "open", "draft": False, "user": {"login": "dependabot[bot]"},
            "head": {"sha": "a" * 40, "repo": {"full_name": "fixture/app"}},
            "base": {"ref": "main", "repo": {"full_name": "fixture/app",
                                               "default_branch": "main"}},
            "mergeable": True, "mergeable_state": "clean",
        }
        self.build = {"name": "Build", "workflow": "Build Check",
                      "bucket": "pass", "state": "SUCCESS"}

    def decide(self, metadata=None, required=None, checks=None):
        """Supply the same independent metadata/check contract as the hosted caller."""
        return POLICY.decision(metadata if metadata is not None else self.pr,
                               required if required is not None else [self.build],
                               checks if checks is not None else [self.build],
                               "a" * 40, POLICY.BOTS["dependabot"])

    def test_only_eligible_current_bot_heads_pass(self):
        """Keep ownership, default branch, draft, identity and mergeability gates."""
        self.assertIsNone(self.decide())
        invalid = [{"state": "closed"}, {"draft": True}, {"user": {"login": "human"}},
                   {"head": {"sha": "b" * 40, "repo": self.pr["head"]["repo"]}},
                   {"head": {"sha": "a" * 40, "repo": {"full_name": "fork/app"}}},
                   {"base": {"ref": "other", "repo": self.pr["base"]["repo"]}},
                   {"mergeable": None}]
        invalid += [{"mergeable_state": value} for value in
                    ("unknown", "blocked", "dirty", "behind", "unstable", None)]
        for change in invalid:
            with self.subTest(change=change):
                self.assertIsNotNone(self.decide(metadata=dict(self.pr, **change)))

    def test_required_build_and_every_check_must_pass(self):
        """An absent, skipped, pending or failed required check never grants a merge."""
        self.assertIsNotNone(self.decide(required=[]))
        self.assertIsNotNone(self.decide(checks=[]))
        self.assertIsNotNone(self.decide(required=[dict(self.build, workflow="Unrelated")]))
        for value in ("pending", "fail", "cancel", "skipping", None):
            self.assertIsNotNone(self.decide(required=[dict(self.build, bucket=value)]))
        for value in ("pending", "fail", "cancel", None):
            self.assertIsNotNone(self.decide(checks=[self.build, {"bucket": value}]))
        for value in ("NEUTRAL", "SKIPPED"):
            self.assertIsNotNone(self.decide(checks=[dict(self.build, state=value)]))
        self.assertIsNone(self.decide(checks=[self.build, {"bucket": "skipping"}]))

    def test_changed_head_or_api_failure_never_requests_merge(self):
        """The final metadata re-read protects against a concurrently updated PR."""
        changed = copy.deepcopy(self.pr)
        changed["head"]["sha"] = "b" * 40
        responses = [self.pr, [self.build], [self.build], changed]
        with patch.object(POLICY, "gh", side_effect=responses) as api:
            result = POLICY.inspect_and_merge("fixture/app", 1, POLICY.BOTS["dependabot"])
            self.assertEqual(result, "PR head changed")
            self.assertEqual(api.call_count, 4)
        with patch.object(POLICY, "gh", side_effect=[self.pr, RuntimeError("offline")]):
            with self.assertRaises(RuntimeError):
                POLICY.inspect_and_merge("fixture/app", 1, POLICY.BOTS["dependabot"])

    def test_success_uses_exact_sha_and_ordinary_merge_rules(self):
        """Keep the exact-head REST request without force or administrator bypass."""
        responses = [self.pr, [self.build], [self.build], self.pr, {"merged": True}]
        with patch.object(POLICY, "gh", side_effect=responses) as api:
            result = POLICY.inspect_and_merge("fixture/app", 1, POLICY.BOTS["dependabot"])
            self.assertEqual(result, "merged checked head")
            self.assertEqual(api.call_args.args, (
                "api", "--method", "PUT", "repos/fixture/app/pulls/1/merge", "-f",
                "merge_method=squash", "-f", "sha=" + "a" * 40,
            ))

    def test_dry_run_never_requests_merge(self):
        """Inspecting an eligible head is still read-only when dry-run is selected."""
        with patch.object(POLICY, "gh", side_effect=[self.pr, [self.build],
                                                   [self.build], self.pr]) as api:
            result = POLICY.inspect_and_merge("fixture/app", 1, POLICY.BOTS["dependabot"],
                                              dry_run=True)
            self.assertIn("dry run", result)
            self.assertEqual(api.call_count, 4)


if __name__ == "__main__":
    unittest.main()
