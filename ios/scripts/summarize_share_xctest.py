"""Summarize strict iOS ShareSheet XCTest results without weakening their gate.

XCTest is the source of pass/fail; app-owned phase traces are a separate source.
No document content, arbitrary assertion strings or URLs are copied to JSON.
"""
from collections import Counter
from pathlib import Path
import json
import re
import sys

CASE = re.compile(
    r"Test Case '-\[(?P<suite>[\w.]+) (?P<name>test\w+)\]' "
    r"(?P<state>started|passed|failed|skipped)(?: \([^\n]*?\))?\."
)
ERROR = re.compile(
    r"\.swift:(?P<line>\d+): error: -\[(?P<suite>[\w.]+) "
    r"(?P<name>test\w+)\] : (?P<message>.*)"
)
TAP = re.compile(
    r"QA_SHARE_OUTSIDE_TAP: strategy=(?P<strategy>edge|interior) "
    r"x=(?P<x>-?\d+(?:\.\d+)?) y=(?P<y>-?\d+(?:\.\d+)?)"
)
MARKER = re.compile(r"QA_SHARE_DISMISSAL_FAILURE: route=(SwiftUI|UIKit) phase=([\w-]+)")
# xcodebuild emits one of these terminal markers after executing XCTest.
# Explicit failure is authoritative even if individual test cases weren't parsed.
TERMINAL = re.compile(r"(?:^|\s)\*\* TEST (SUCCEEDED|FAILED) \*\*\s*$")


def classify(message: str) -> str:
    """Return an evidence category; never return untrusted assertion text."""
    lower = message.lower()
    if "failed to get matching snapshot" in lower or "failed to resolve remote element" in lower:
        return "xctest_remote_ax_snapshot"
    if "xctassertgreaterthanorequal failed" in lower:
        return "undersized_hit_target"
    if "must be enabled" in lower or "fully loaded cold-launch reader" in lower:
        return "reader_control_not_ready"
    if "must physically dismiss" in lower or "must close and restore" in lower:
        return "native_share_dismissal_failed"
    if "hittable native system close" in lower or "hittable close" in lower:
        return "native_close_unavailable"
    if "usable real share action" in lower or "share actions" in lower:
        return "native_share_action_unavailable"
    if "activitylistview must appear" in lower or "actual system share container must appear" in lower:
        return "native_share_container_unavailable"
    return "other_assertion"


def summarize(raw: str | None) -> dict:
    if raw is None:
        return {"schema": 1, "status": "unavailable", "verdict": "unknown",
                "xcodebuild_result": "unobserved",
                "counts": {"passed": 0, "failed": 0, "skipped": 0, "incomplete": 0},
                "failure_categories": {}, "tests": [],
                "caution": "No XCTest log available; absence is not a pass."}
    tests = []
    active = None
    terminal_results = set()
    for line in raw.splitlines():
        terminal = TERMINAL.search(line)
        if terminal:
            terminal_results.add(terminal.group(1))
        event = CASE.search(line)
        if event:
            suite, name, state = event.group("suite", "name", "state")
            if state == "started":
                active = {"suite": suite, "name": name, "outcome": "incomplete",
                          "errors": [], "taps": [], "dismissal_failure_markers": []}
                tests.append(active)
            else:
                matching = next((t for t in reversed(tests)
                                 if t["suite"] == suite and t["name"] == name
                                 and t["outcome"] == "incomplete"), None)
                if matching:
                    matching["outcome"] = state
                    if matching is active:
                        active = None
            continue
        error = ERROR.search(line)
        if error:
            suite, name = error.group("suite", "name")
            matching = next((t for t in reversed(tests)
                             if t["suite"] == suite and t["name"] == name
                             and t["outcome"] == "incomplete"), None)
            if matching:
                matching["errors"].append({
                    "source_line": int(error.group("line")),
                    "category": classify(error.group("message")),
                })
            continue
        if active is not None:
            tap = TAP.search(line)
            if tap:
                active["taps"].append({"strategy": tap.group("strategy"),
                                       "x": float(tap.group("x")),
                                       "y": float(tap.group("y"))})
            marker = MARKER.search(line)
            if marker:
                active["dismissal_failure_markers"].append({
                    "route": marker.group(1), "phase": marker.group(2)})
    counts = Counter(t["outcome"] for t in tests)
    cats = Counter(e["category"] for t in tests for e in t["errors"])
    xcodebuild_result = ("failed" if "FAILED" in terminal_results else
                         "succeeded" if "SUCCEEDED" in terminal_results else "unobserved")
    verdict = ("fail" if counts["failed"] or xcodebuild_result == "failed" else
               "pass" if counts["passed"] and not counts["incomplete"] else "unknown")
    return {
        "schema": 1,
        "status": "ok" if tests and not counts["incomplete"] else ("partial" if tests else "empty"),
        "verdict": verdict,
        "xcodebuild_result": xcodebuild_result,
        "counts": {k: counts[k] for k in ("passed", "failed", "skipped", "incomplete")},
        "failure_categories": dict(sorted(cats.items())),
        "tests": tests,
        "caution": ("XCTest pass/fail is authoritative only for this run. App-owned "
                    "lifecycle callbacks cannot prove physical dismissal or "
                    "identify a framework root cause. AX snapshot errors are "
                    "not proof of blank native UI."),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: summarize_share_xctest.py INPUT_LOG OUTPUT_JSON")
    source, destination = (Path(s) for s in sys.argv[1:])
    result = summarize(source.read_text(encoding="utf-8", errors="replace")
                       if source.is_file() else None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, sort_keys=True, indent=2,
                                      ensure_ascii=False) + "\n", encoding="utf-8")
    print("QA_SHARE_XCTEST_SUMMARY", "status=" + result["status"],
          "verdict=" + result["verdict"],
          "failed=" + str(result["counts"]["failed"]), flush=True)


if __name__ == "__main__":
    main()
