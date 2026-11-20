"""Summarize only opt-in, app-owned iOS ShareSheet lifecycle evidence.

A missing terminal event is *not* evidence of an Apple framework root cause:
XCTest can terminate the process, and system UI may be detached separately.
The raw app-owned log remains the primary record.
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys

LINE = re.compile(
    r"^(?P<epoch>\d{10}(?:\.\d+)?) pid=(?P<pid>\d+) "
    r"(?P<event>[A-Za-z][A-Za-z0-9-]*)(?: .*)?$"
)
UNAVAILABLE = "QA_SHARE_LIFECYCLE_FILE_UNAVAILABLE"


def summarize(raw: str) -> dict:
    """Return a structured summary without copying event parameters or URLs."""
    if raw.strip() == UNAVAILABLE:
        return {
            "schema": 1, "status": "unavailable", "parsed_lines": 0,
            "unparsed_lines": 0, "processes": [], "by_route": {},
            "caution": "No app-owned lifecycle evidence was captured."
        }
    groups = defaultdict(list)
    malformed = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        match = LINE.fullmatch(line)
        if match is None:
            malformed += 1
            continue
        groups[match.group("pid")].append(
            (float(match.group("epoch")), match.group("event"))
        )

    processes = []
    aggregate = {
        "swiftui": {"processes": 0, "controller_created": 0,
                    "presentation_callback": 0, "completion_observed": 0,
                    "completion_not_recorded": 0},
        "direct-uikit": {"processes": 0, "controller_created": 0,
                         "presentation_callback": 0, "completion_observed": 0,
                         "completion_not_recorded": 0},
    }
    for pid, observations in groups.items():
        observations.sort()
        names = {name for _, name in observations}
        route = ("direct-uikit" if any(name.startswith("direct-uikit-")
                                       for name in names) else "swiftui")
        created = ("direct-uikit-controller-created" in names if route == "direct-uikit"
                   else "representable-return-activity-view-controller" in names)
        presented = ("direct-uikit-presentation-completed" in names
                     if route == "direct-uikit" else False)
        completion = ("direct-uikit-completion" in names if route == "direct-uikit"
                      else "swiftui-onDismiss" in names)
        row = aggregate[route]
        row["processes"] += 1
        row["controller_created"] += int(created)
        row["presentation_callback"] += int(presented)
        row["completion_observed"] += int(completion)
        row["completion_not_recorded"] += int(not completion)
        processes.append({
            "pid": int(pid),
            "route": route,
            "first_event_utc": datetime.fromtimestamp(
                observations[0][0], tz=timezone.utc
            ).isoformat(timespec="milliseconds"),
            "last_recorded_event": observations[-1][1],
            "recorded_event_count": len(observations),
            "controller_created": created,
            "presentation_callback_observed": presented if route == "direct-uikit" else None,
            "dismissal_or_completion_observed": completion,
            "completion_marker_not_recorded": not completion,
        })
    processes.sort(key=lambda p: (p["first_event_utc"], p["pid"]))
    return {
        "schema": 1,
        "status": "partial" if malformed else ("ok" if groups else "empty"),
        "parsed_lines": sum(len(v) for v in groups.values()),
        "unparsed_lines": malformed,
        "by_route": aggregate,
        "processes": processes,
        "caution": (
            "Absence of an app callback does not independently prove the "
            "cause of a ShareSheet failure; correlate with strict XCTest "
            "assertions, screenshots and accessibility hierarchy."
        ),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: summarize_share_lifecycle.py INPUT_LOG OUTPUT_JSON")
    source, target = (Path(arg) for arg in sys.argv[1:])
    result = summarize(source.read_text(encoding="utf-8"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "QA_SHARE_PHASE_SUMMARY",
        "status=" + result["status"],
        "processes=" + str(len(result["processes"])),
        "unparsed_lines=" + str(result["unparsed_lines"]),
        flush=True,
    )


if __name__ == "__main__":
    main()
