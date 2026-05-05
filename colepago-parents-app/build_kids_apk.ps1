# PowerShell script to build the kids APK and rename it

# Navigate to the Flutter project root
you can change this path if needed
cd d:/kidwall/colepago-parents-app

# Build the APK
flutter build apk --flavor kids --target lib/main_kid.dart --dart-define=FLAVOR=kids

# Rename the APK if build succeeded
$apkPath = "build/app/outputs/flutter-apk/app-release.apk"
$kidsApkPath = "build/app/outputs/flutter-apk/app-kids-release.apk"

if (Test-Path $apkPath) {
    Rename-Item -Path $apkPath -NewName "app-kids-release.apk" -Force
    Write-Host "APK renamed to app-kids-release.apk"
} else {
    Write-Host "Build failed or APK not found."
}
