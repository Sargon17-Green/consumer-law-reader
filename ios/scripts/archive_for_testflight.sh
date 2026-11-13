#!/usr/bin/env bash
# Run on a Mac with Xcode, XcodeGen, and an Apple Developer Program account.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "$APPLE_TEAM_ID"
: "$IOS_BUNDLE_ID"
command -v xcodebuild >/dev/null || { echo "Install Xcode first." >&2; exit 2; }
command -v xcodegen >/dev/null || { echo "XcodeGen2.46.0 is required; use the checksum-pinned installation in .github/workflows/ios-ci.yml." >&2; exit 2; }
[[ "$(xcodegen --version)" == 'Version: 2.46.0' ]] || { echo "Use XcodeGen2.46.0, matching the tested CI generator." >&2; exit 2; }
cd "$ROOT"
python3 -m pip install -r requirements-qa.txt
python3 scripts/build_web.py
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -p 'test_ios_source.py' -v
bash ios/scripts/prepare_assets.sh
xcodegen generate --spec ios/project.yml --project ios
mkdir -p build/ios
xcodebuild \
  -project ios/ConsumerLawReader.xcodeproj \
  -scheme ConsumerLawReader \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath "$ROOT/build/ios/ConsumerLawReader.xcarchive" \
  -allowProvisioningUpdates \
  DEVELOPMENT_TEAM="$APPLE_TEAM_ID" \
  PRODUCT_BUNDLE_IDENTIFIER="$IOS_BUNDLE_ID" \
  CODE_SIGN_STYLE=Automatic \
  archive
echo "Archive ready: $ROOT/build/ios/ConsumerLawReader.xcarchive"
echo "In Xcode > Window > Organizer > Archives, select Distribute App > TestFlight & App Store > Upload."
echo "A TestFlight link exists only after App Store Connect processes and enables the build."
