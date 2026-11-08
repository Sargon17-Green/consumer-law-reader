#!/usr/bin/env bash
set -euo pipefail
# This configures only a disposable, writable Android 8 AOSP CI emulator.
[[ "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" == 26 ]]
[[ "$(adb shell getprop ro.debuggable | tr -d '\r')" == 1 ]]
[[ "$(adb shell getprop ro.kernel.qemu | tr -d '\r')" == 1 ]]
SDK=.toolchain/build-tools-36.0.0/android-16
OLD="$(adb shell pm path com.android.webview | tr -d '\r' | sed -n 's/^package://p' | head -1)"
OUTPUT="$(adb install -r -t build/api26-test-webview.apk 2>&1)" && INSTALLED=true || INSTALLED=false
if [[ "$INSTALLED" != true ]]; then
  if [[ "$OUTPUT" != *INSTALL_FAILED_UPDATE_INCOMPATIBLE* ]]; then
    printf '%s\n' "$OUTPUT"
    exit 1
  fi
  case "$OLD" in
    /system/app/webview/*.apk|/system/app/WebView/*.apk) ;;
    *) printf 'Unexpected test provider path: %s\n' "$OLD"; exit 1 ;;
  esac
  adb root
  adb wait-for-device
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
  adb shell cmd webviewupdate enable-redundant-packages
  adb install -t build/api26-test-webview.apk
fi
adb shell cmd webviewupdate enable-redundant-packages
adb shell pm enable com.android.webview
adb shell dumpsys package com.android.webview > evidence/api26-provider-package.txt
if ! adb shell cmd webviewupdate set-webview-implementation com.android.webview | grep -q 'Success'; then
  # The SDK image's framework lists only Google-branded packages although its
  # factory APK is com.android.webview. Installing the unmodified official AOSP
  # provider cannot fix that mismatch. Use a resource-only system overlay for
  # this test image, following Chromium's AOSP integration configuration.
  # No app security policy, provider bytes, minSdk or production system changes.
  adb root
  adb wait-for-device
  adb remount
  adb pull /system/framework/framework-res.apk build/api26-framework-res.apk
  "$SDK/aapt2" dump xmltree build/api26-framework-res.apk --file res/xml/config_webview_packages.xml > evidence/api26-framework-providers.txt
  if grep -q 'packageName="com.android.webview"' evidence/api26-framework-providers.txt; then
    cat evidence/api26-framework-providers.txt
    echo "AOSP provider is already configured; refusing an unexplained replacement."
    exit 1
  fi
  mkdir -p build/api26-provider-overlay/res/xml
  cat > build/api26-provider-overlay/AndroidManifest.xml <<'XML'
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="il.org.lawreader.qa.webviewprovider" android:versionCode="1" android:versionName="1">
  <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="26"/>
  <overlay android:targetPackage="android" android:isStatic="true" android:priority="999"/>
  <application android:hasCode="false"/>
</manifest>
XML
  cat > build/api26-provider-overlay/res/xml/config_webview_packages.xml <<'XML'
<webviewproviders>
  <webviewprovider packageName="com.android.webview" description="Official AOSP WebView (CI)" availableByDefault="true"/>
</webviewproviders>
XML
  "$SDK/aapt2" compile --dir build/api26-provider-overlay/res -o build/api26-provider-overlay/resources.zip
  "$SDK/aapt2" link -I build/api26-framework-res.apk --manifest build/api26-provider-overlay/AndroidManifest.xml --auto-add-overlay -o build/api26-provider-overlay/unsigned.apk build/api26-provider-overlay/resources.zip
  "$SDK/zipalign" -f 4 build/api26-provider-overlay/unsigned.apk build/api26-provider-overlay/aligned.apk
  java -jar "$SDK/lib/apksigner.jar" sign --ks build/qa-debug-keystore.p12 --ks-key-alias qa-debug --ks-pass pass:qa-only-password --v4-signing-enabled false --out build/api26-provider-overlay/ReaderQAWebView.apk build/api26-provider-overlay/aligned.apk
  adb shell mkdir -p /vendor/overlay
  adb push build/api26-provider-overlay/ReaderQAWebView.apk /vendor/overlay/ReaderQAWebView.apk
  adb shell chmod 644 /vendor/overlay/ReaderQAWebView.apk
  adb shell restorecon /vendor/overlay/ReaderQAWebView.apk
  adb reboot
  adb wait-for-device
  for ((i=0;i<90;i++)); do
    [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]] && break
    sleep 2
  done
  [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]
  adb shell cmd webviewupdate enable-redundant-packages
  adb shell pm enable com.android.webview
  adb shell cmd overlay list | tee evidence/api26-system-overlay.txt
  adb shell dumpsys overlay > evidence/api26-system-overlay-details.txt
  adb shell pm path il.org.lawreader.qa.webviewprovider | tee evidence/api26-system-overlay-path.txt
  grep -q ReaderQAWebView.apk evidence/api26-system-overlay-path.txt
  printf '{"api":26,"officialAospProvider":true,"resourceOnlyTestImageOverlay":true,"stockRetailImage":false}\n' > evidence/api26-environment.json
fi
SELECTED=false
for ((i=0;i<40;i++)); do
  if adb shell cmd webviewupdate set-webview-implementation com.android.webview | tee evidence/api26-provider-selection.txt | grep -q 'Success'; then
    SELECTED=true
    break
  fi
  sleep 0.5
done
adb shell dumpsys webviewupdate | tee evidence/api26-provider-selected.txt
[[ "$SELECTED" == true ]]
grep -q 'Current WebView package.*com.android.webview' evidence/api26-provider-selected.txt
