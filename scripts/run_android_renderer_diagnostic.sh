#!/usr/bin/env bash
set -euo pipefail
mkdir -p evidence
collect() {
  adb logcat -d -v threadtime > evidence/android-renderer-logcat.txt 2>&1 || true
  adb exec-out run-as il.org.lawreader.consumer cat files/qa-failure.png > evidence/android-renderer-failure.png 2>/dev/null || true
  adb shell dumpsys webviewupdate > evidence/android-renderer-provider.txt 2>&1 || true
}
trap collect EXIT
adb install build/android-qa/reader-qa.apk
adb install debug-build/*DEBUG_NOT_FOR_UPGRADE.apk
adb shell cmd connectivity airplane-mode enable
adb shell svc wifi disable
adb shell svc data disable
python - <<'NET'
from pathlib import Path
import re,subprocess,time
for attempt in range(60):
    text=subprocess.check_output(['adb','shell','dumpsys','connectivity']).decode(errors='replace')
    Path('evidence/android-renderer-offline.txt').write_text(text)
    if re.search(r'Active default network:\s*(none|null|-1)',text,re.I):break
    time.sleep(.5)
else:raise AssertionError('No proof of offline network state')
NET
adb shell am instrument -w -e rendererOnly true il.org.lawreader.consumer.qa/.ReaderInstrumentation | tee evidence/android-renderer-instrumentation.txt
grep -q 'QA_STATUS=PASS' evidence/android-renderer-instrumentation.txt
