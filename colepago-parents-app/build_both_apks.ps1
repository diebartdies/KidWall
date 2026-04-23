# PowerShell script to build both kids and parents APKs using Flutter flavors

$projectPath = "d:/kidwall/colepago-parents-app"
Set-Location $projectPath

# Build Kids APK (full UX)
flutter build apk --flavor kids --target lib/main.dart --dart-define=FLAVOR=kids
$kidsApk = "$projectPath/build/app/outputs/flutter-apk/app-kids-release.apk"
if (Test-Path $kidsApk) {
    Write-Host "Kids APK generated: $kidsApk"
} elseif (Test-Path "$projectPath/build/app/outputs/flutter-apk/app-release.apk") {
    Rename-Item "$projectPath/build/app/outputs/flutter-apk/app-release.apk" "$kidsApk" -Force
    Write-Host "Kids APK renamed to app-kids-release.apk"
} else {
    Write-Host "Kids APK build failed."
}

# Build Parents APK
flutter build apk --flavor parents --target lib/main_parent.dart --dart-define=FLAVOR=parents
$parentsApk = "$projectPath/build/app/outputs/flutter-apk/app-parents-release.apk"
if (Test-Path $parentsApk) {
    Write-Host "Parents APK generated: $parentsApk"
} elseif (Test-Path "$projectPath/build/app/outputs/flutter-apk/app-release.apk") {
    Rename-Item "$projectPath/build/app/outputs/flutter-apk/app-release.apk" "$parentsApk" -Force
    Write-Host "Parents APK renamed to app-parents-release.apk"
} else {
    Write-Host "Parents APK build failed."
}

Write-Host "Build process complete."
Write-Host "Kids APK: $kidsApk"
Write-Host "Parents APK: $parentsApk"
