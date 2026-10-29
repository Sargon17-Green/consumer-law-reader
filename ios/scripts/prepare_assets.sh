#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT="$ROOT/web/icon-512.png"
OUTPUT="$ROOT/ios/ConsumerLawReader/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Native iOS icon preparation requires macOS/sips." >&2
  exit 2
fi
test -s "$INPUT"
mkdir -p "$(dirname "$OUTPUT")"
sips --resampleHeightWidth 1024 1024 "$INPUT" --out "$OUTPUT" >/dev/null
test -s "$OUTPUT"
sips -g pixelWidth -g pixelHeight "$OUTPUT"
