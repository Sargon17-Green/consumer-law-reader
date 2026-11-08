#!/usr/bin/env bash
set -euo pipefail
# Only the fresh API 26 AOSP CI emulator is passed here.
[[ "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" == 26 ]]
[[ "$(adb shell getprop ro.debuggable | tr -d '\r')" == 1 ]]
OLD="$(adb shell pm path com.android.webview | tr -d '\r' | sed -n 's/^package://p' | head -1)"
OUTPUT="$(adb install -r -t build/api26-test-webview.apk 2>&1)" && INSTALLED=true || INSTALLED=false
if [[ "$INSTALLED" != true ]]; then
  if [[ "$OUTPUT" != *INSTALL_FAILED_UPDATE_INCOMPATIBLE* ]]; then
    printf '%s\n' "$OUTPUT"
    exit 1
  fi
  # Chromium's official provider instructions permit removing a conflicting
  # preinstalled provider on userdebug images. Never alter an unrelated path.
  case "$OLD" in
    /system/app/webview/*.apk|/system/app/WebView/*.apk) ;;
    *) printf 'Unexpected preinstalled test provider path: %s\n' "$OLD"; exit 1 ;;
  esac
  adb root
  adb wait-for-device
  # Follow Chromium's developer-only system-app removal sequence. A normal
  # emulator system partition is reverted on reboot; CI starts this one writable.
  adb disable-verity
  adb remount
  adb shell stop
  adb shell rm "$OLD"
  adb reboot
  adb wait-for-device
  for ((i=0;i<90;i++)); do
    [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]] && break
    sleep 2
  done
  [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]
  adb root
  adb wait-for-device
  if adb shell test -f "$OLD"; then
    printf 'System WebView removal did not persist: %s\n' "$OLD"
    exit 1
  fi
  # Chromium's provider setup also disables Nougat/Oreo fallback logic; that
  # logic can otherwise disable/remove a newly installed standalone provider.
  adb shell cmd webviewupdate enable-redundant-packages
  adb install -t build/api26-test-webview.apk
fi
adb shell cmd webviewupdate enable-redundant-packages
adb shell pm enable com.android.webview
adb shell dumpsys package com.android.webview > evidence/api26-provider-package.txt
# Some Oreo images enumerate only factory providers. Restore the *same official
# test APK* at the original factory location, never edit the framework allowlist.
if ! adb shell cmd webviewupdate set-webview-implementation com.android.webview | grep -q 'Success'; then
  case "$OLD" in /system/app/webview/*.apk|/system/app/WebView/*.apk) ;; *) exit 1 ;; esac
  adb root
  adb wait-for-device
  adb remount
  adb shell df -h /system > evidence/api26-system-space.txt
  adb shell ls -lR "$(dirname "$OLD")" > evidence/api26-original-provider-files.txt
  adb pull /system/framework/framework-res.apk build/api26-framework-res.apk
  .toolchain/build-tools-36.0.0/android-16/aapt2 dump xmltree build/api26-framework-res.apk --file res/xml/config_webview_packages.xml > evidence/api26-framework-providers.txt 2>&1 || true
  adb shell stop
  # A leftover factory library must not override the new APK's bundled library.
  adb shell rm -rf "$(dirname "$OLD")/lib"
  adb push build/api26-test-webview.apk "$OLD"
  adb shell chmod 644 "$OLD"
  adb shell restorecon "$OLD"
  adb reboot
  adb wait-for-device
  for ((i=0;i<90;i++)); do
    [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]] && break
    sleep 2
  done
  [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]
  adb shell cmd webviewupdate enable-redundant-packages
  adb shell pm enable com.android.webview
  adb shell dumpsys package com.android.webview > evidence/api26-factory-provider-package.txt
fi
# Package broadcasts and RELRO preparation complete asynchronously after install.
SELECTED=false
for ((i=0;i<40;i++)); do
  if adb shell cmd webviewupdate set-webview-implementation com.android.webview | tee evidence/api26-provider-selection.txt | grep -q 'Success'; then
    SELECTED=true
    break
  fi
  sleep 0.5
done
adb shell dumpsys webviewupdate > evidence/api26-provider-selected.txt
[[ "$SELECTED" == true ]]
grep -q 'Current WebView package.*com.android.webview' evidence/api26-provider-selected.txt
