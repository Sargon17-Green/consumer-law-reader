#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
collect() {
  adb logcat -d -v threadtime > evidence/android-logcat.txt 2>&1 || true
  adb shell dumpsys meminfo il.org.lawreader.consumer > evidence/android-memory.txt 2>&1 || true
  adb shell dumpsys webviewupdate > evidence/android-webview.txt 2>&1 || true
  adb exec-out screencap -p > evidence/android-emulator.png 2>/dev/null || true
}
trap collect EXIT
adb install build/android-qa/reader-qa.apk
adb install build/qa-upgrade-old.apk
adb shell am instrument -w -e seed true il.org.lawreader.consumer.qa/.ReaderInstrumentation | tee evidence/android-upgrade-seed.txt
grep -q 'QA_STATUS=PASS' evidence/android-upgrade-seed.txt
adb install -r debug-build/*DEBUG_NOT_FOR_UPGRADE.apk
EXPECT_DATE=$(python tests/date_network_probe.py)
adb shell am instrument -w -e verifyUpgrade true -e expectDate "$EXPECT_DATE" il.org.lawreader.consumer.qa/.ReaderInstrumentation | tee evidence/android-online-instrumentation.txt
grep -q 'QA_STATUS=PASS' evidence/android-online-instrumentation.txt
if [[ "$1" == 26 ]]; then
  adb root
  adb wait-for-device
  adb shell settings put global airplane_mode_on 1
  adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true
else
  adb shell svc wifi disable
  adb shell svc data disable
fi
adb shell dumpsys connectivity > evidence/android-offline-connectivity.txt
python - <<'PY'
from pathlib import Path
import re
text=Path('evidence/android-offline-connectivity.txt').read_text()
assert re.search(r'Active default network:\s*(none|null|-1)',text,re.I),'No proof of offline network state; see connectivity dump'
PY
adb shell am instrument -w il.org.lawreader.consumer.qa/.ReaderInstrumentation | tee evidence/android-instrumentation.txt
grep -q 'QA_STATUS=PASS' evidence/android-instrumentation.txt
