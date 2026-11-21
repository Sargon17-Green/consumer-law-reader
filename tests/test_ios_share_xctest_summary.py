"""No-network tests for strict iOS ShareSheet XCTest evidence classification."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "share_xctest_summary_qa", ROOT / "ios/scripts/summarize_share_xctest.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def started(name):
    return f"Test Case '-[ConsumerLawReaderUITests.ReaderUITests {name}]' started."


def ended(name, result):
    return f"Test Case '-[ConsumerLawReaderUITests.ReaderUITests {name}]' {result} (12.3 seconds)."


def failure(name, line, text):
    return (f"ios/ConsumerLawReaderUITests/ReaderUITests.swift:{line}: error: "
            f"-[ConsumerLawReaderUITests.ReaderUITests {name}] : {text}")


class ShareXCTestSummaryTests(unittest.TestCase):
    def test_actual_popover_dismissal_failure_retains_tap_without_raw_assertion(self):
        name = "testQAUIKitDirectShareAfterColdLaunch"
        raw = "\n".join([started(name),
            "QA_SHARE_OUTSIDE_TAP: strategy=edge x=15.0 y=150.0 popoverFrame=(1,2,3,4)",
            "QA_SHARE_DISMISSAL_FAILURE: route=UIKit phase=outside-tap activityExists=true",
            failure(name, 378, "Native popover must physically dismiss and restore reader SECRET_URL"),
            ended(name, "failed")])
        result = MODULE.summarize(raw)
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["failure_categories"], {"native_share_dismissal_failed": 1})
        self.assertEqual(result["tests"][0]["taps"],
                         [{"strategy": "edge", "x": 15., "y": 150.}])
        self.assertEqual(result["tests"][0]["errors"][0]["source_line"], 378)
        self.assertNotIn("SECRET_URL", str(result))

    def test_ax_snapshot_interruption_is_not_claimed_as_blank_share(self):
        name = "testQAShareRepeatABUIKitFirst"
        report = MODULE.summarize("\n".join([started(name), failure(name, 309,
            "Failed to get matching snapshot: Failed to resolve remote element AX element"),
            ended(name, "failed")]))
        self.assertEqual(report["failure_categories"], {"xctest_remote_ax_snapshot": 1})

    def test_control_not_ready_and_hit_target_are_distinct(self):
        a, b = "testNativeShareDirectlyAfterColdLaunch", "testNativeShareAfterFileImporterWithoutPrint"
        report = MODULE.summarize("\n".join([
            started(a), failure(a, 185, "Native share must be enabled on the fully loaded cold-launch reader"), ended(a, "failed"),
            started(b), failure(b, 55, 'XCTAssertGreaterThanOrEqual failed: ("41.89") is less than ("44.0")'), ended(b, "failed")]))
        self.assertEqual(report["failure_categories"],
                         {"reader_control_not_ready": 1, "undersized_hit_target": 1})

    def test_pass_and_skip_do_not_turn_into_failures(self):
        a, b = "testQAUIKitDirectShareAfterColdLaunch", "testQAUIKitInteriorOutsideTapRepeatTwo"
        report = MODULE.summarize("\n".join([started(a), ended(a, "passed"),
                                              started(b), ended(b, "skipped")]))
        self.assertEqual(report["verdict"], "pass")
        self.assertEqual(report["counts"], {"passed": 1, "failed": 0, "skipped": 1, "incomplete": 0})

    def test_missing_and_empty_logs_are_never_pass(self):
        self.assertEqual(MODULE.summarize(None)["status"], "unavailable")
        self.assertEqual(MODULE.summarize(None)["verdict"], "unknown")
        self.assertEqual(MODULE.summarize("")["status"], "empty")
        self.assertEqual(MODULE.summarize("")["verdict"], "unknown")

    def test_all_skipped_does_not_count_as_test_pass(self):
        name = "testQAUIKitInteriorOutsideTapRepeatTwo"
        report = MODULE.summarize("\n".join([started(name), ended(name, "skipped"),
                                                   "** TEST SUCCEEDED **"]))
        self.assertEqual(report["counts"]["passed"], 0)
        self.assertEqual(report["counts"]["skipped"], 1)
        self.assertEqual(report["xcodebuild_result"], "succeeded")
        self.assertEqual(report["verdict"], "unknown")

    def test_xcodebuild_failure_cannot_be_overridden_by_parsed_pass(self):
        name = "testQAUIKitDirectShareAfterColdLaunch"
        report = MODULE.summarize("\n".join([started(name), ended(name, "passed"),
                                                   "** TEST FAILED **"]))
        self.assertEqual(report["counts"]["failed"], 0)
        self.assertEqual(report["xcodebuild_result"], "failed")
        self.assertEqual(report["verdict"], "fail")

    def test_xcodebuild_failure_without_test_events_is_not_unknown_or_pass(self):
        report = MODULE.summarize("2026-11-21T07:04:54Z ** TEST FAILED **\n")
        self.assertEqual(report["status"], "empty")
        self.assertEqual(report["xcodebuild_result"], "failed")
        self.assertEqual(report["verdict"], "fail")

    def test_explicit_success_without_any_executed_test_is_not_a_pass(self):
        report = MODULE.summarize("** TEST SUCCEEDED **\n")
        self.assertEqual(report["xcodebuild_result"], "succeeded")
        self.assertEqual(report["verdict"], "unknown")

    def test_interrupted_or_retried_test_is_not_silently_accepted(self):
        name = "testQAShareRepeatABSwiftUIFirst"
        report = MODULE.summarize(started(name) + "\n")
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["counts"]["incomplete"], 1)
        self.assertEqual(report["verdict"], "unknown")
        retried = MODULE.summarize("\n".join([started(name), ended(name, "failed"),
                                               started(name), ended(name, "passed")]))
        self.assertEqual(retried["counts"]["failed"], 1)
        self.assertEqual(retried["verdict"], "fail")

    def test_unknown_assertion_does_not_leak_message(self):
        name = "testNativeShareDirectlyAfterColdLaunch"
        report = MODULE.summarize("\n".join([started(name), failure(name, 99,
             "USER_PROVIDED_DOCUMENT_TEXT DO NOT EXPORT"), ended(name, "failed")]))
        self.assertEqual(report["failure_categories"], {"other_assertion": 1})
        self.assertNotIn("USER_PROVIDED_DOCUMENT_TEXT", str(report))


if __name__ == "__main__":
    unittest.main()
