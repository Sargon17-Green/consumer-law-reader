"""No-network contract tests for app-owned ShareSheet lifecycle summaries."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "share_lifecycle_summary_qa", ROOT / "ios/scripts/summarize_share_lifecycle.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def entry(pid, epoch, event):
    return f"{epoch:.3f} pid={pid} {event}"


class ShareLifecycleSummaryTests(unittest.TestCase):
    def test_swiftui_created_but_no_dismissal_is_not_counted_as_success(self):
        raw = "\n".join([
            entry(100, 1795203162.867, "reader-share-action-enter ready=true"),
            entry(100, 1795203162.921, "reader-share-payload-assigned"),
            entry(100, 1795203163.022, "representable-make-activity-view-controller"),
            entry(100, 1795203163.030, "representable-return-activity-view-controller"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["by_route"]["swiftui"]["controller_created"], 1)
        self.assertEqual(report["by_route"]["swiftui"]["completion_not_recorded"], 1)
        self.assertFalse(report["processes"][0]["native_activity_callback_observed"])
        self.assertFalse(report["processes"][0]["swiftui_on_dismiss_observed"])

    def test_swiftui_real_dismissal_is_counted_once(self):
        raw = "\n".join([
            entry(101, 1795203162.0, "reader-share-action-enter ready=true"),
            entry(101, 1795203163.0, "representable-return-activity-view-controller"),
            entry(101, 1795203165.0, "swiftui-onDismiss"),
            entry(101, 1795203165.2, "activity-completion-callback completed=false failure=false"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["by_route"]["swiftui"]["completion_observed"], 1)
        self.assertEqual(report["by_route"]["swiftui"]["completion_not_recorded"], 0)
        self.assertEqual(report["by_route"]["swiftui"]["swiftui_on_dismiss_observed"], 1)
        self.assertEqual(report["by_route"]["swiftui"]["native_activity_callback_observed"], 1)

    def test_swiftui_on_dismiss_without_native_callback_is_not_completion(self):
        raw = "\n".join([
            entry(105, 1795203170.0, "representable-return-activity-view-controller"),
            entry(105, 1795203171.0, "swiftui-onDismiss"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["schema"], 2)
        self.assertEqual(report["by_route"]["swiftui"]["completion_observed"], 0)
        self.assertEqual(report["by_route"]["swiftui"]["completion_not_recorded"], 1)
        self.assertEqual(report["by_route"]["swiftui"]["swiftui_on_dismiss_observed"], 1)
        self.assertFalse(report["processes"][0]["native_activity_callback_observed"])
        self.assertTrue(report["processes"][0]["swiftui_on_dismiss_observed"])

    def test_native_activity_callback_without_swiftui_on_dismiss_is_distinct(self):
        raw = "\n".join([
            entry(106, 1795203180.0, "representable-return-activity-view-controller"),
            entry(106, 1795203181.0, "activity-completion-callback completed=false failure=false"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["by_route"]["swiftui"]["completion_observed"], 1)
        self.assertEqual(report["by_route"]["swiftui"]["swiftui_on_dismiss_observed"], 0)
        self.assertTrue(report["processes"][0]["native_activity_callback_observed"])
        self.assertFalse(report["processes"][0]["swiftui_on_dismiss_observed"])

    def test_uikit_presentation_callback_is_not_completion(self):
        raw = "\n".join([
            entry(102, 1795203162.0, "direct-uikit-presentation-requested"),
            entry(102, 1795203163.0, "direct-uikit-controller-created"),
            entry(102, 1795203164.0, "direct-uikit-present-called"),
            entry(102, 1795203165.0, "direct-uikit-presentation-completed"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["by_route"]["direct-uikit"]["presentation_callback"], 1)
        self.assertEqual(report["by_route"]["direct-uikit"]["completion_observed"], 0)
        self.assertTrue(report["processes"][0]["completion_marker_not_recorded"])

    def test_uikit_completion_is_a_separate_event(self):
        raw = "\n".join([
            entry(103, 1795203162.0, "direct-uikit-controller-created"),
            entry(103, 1795203165.0, "direct-uikit-presentation-completed"),
            entry(103, 1795203168.0, "direct-uikit-completion completed=false failure=false"),
        ])
        report = MODULE.summarize(raw)
        self.assertEqual(report["by_route"]["direct-uikit"]["completion_observed"], 1)
        self.assertFalse(report["processes"][0]["completion_marker_not_recorded"])

    def test_direct_uikit_payload_kind_is_observed_not_assumed(self):
        raw = "\n".join([
            entry(301, 1795203162.0, "direct-uikit-payload-string"),
            entry(301, 1795203163.0, "direct-uikit-controller-created"),
            entry(302, 1795203164.0, "direct-uikit-payload-url"),
            entry(302, 1795203165.0, "direct-uikit-controller-created"),
            entry(303, 1795203166.0, "direct-uikit-controller-created"),
        ])
        report = MODULE.summarize(raw)
        by_pid = {p["pid"]: p for p in report["processes"]}
        self.assertEqual(by_pid[301]["payload_kind"], "string")
        self.assertEqual(by_pid[302]["payload_kind"], "url")
        self.assertIsNone(by_pid[303]["payload_kind"])
        self.assertEqual(report["by_route"]["direct-uikit"]["processes"], 3)

    def test_missing_trace_is_not_misreported_as_success(self):
        report = MODULE.summarize("QA_SHARE_LIFECYCLE_FILE_UNAVAILABLE\n")
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["processes"], [])
        self.assertEqual(report["by_route"], {})

    def test_malformed_line_count_does_not_reveal_raw_text(self):
        raw = (
            entry(104, 1795203162.0, "reader-share-action-enter") +
            "\nPERSONAL_URL_SHOULD_NOT_LEAK\n"
        )
        report = MODULE.summarize(raw)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["unparsed_lines"], 1)
        self.assertNotIn("PERSONAL_URL_SHOULD_NOT_LEAK", str(report))


if __name__ == "__main__":
    unittest.main()
