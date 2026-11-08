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
  adb remount
  adb shell rm "$OLD"
  adb reboot
  adb wait-for-device
  for ((i=0;i<90;i++)); do
    [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]] && break
    sleep 2
  done
  [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]
  adb install -t build/api26-test-webview.apk
fi
adb shell cmd webviewupdate set-webview-implementation com.android.webview
adb shell dumpsys webviewupdate > evidence/api26-provider-selected.txt
grep -q 'com.android.webview' evidence/api26-provider-selected.txt
