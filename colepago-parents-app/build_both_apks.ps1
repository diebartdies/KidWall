# PowerShell script to build both kids and parents Android release artifacts using Flutter flavors.
# Generates APKs for direct install/testing and AABs for Google Play upload.
$ErrorActionPreference = "Stop"

$projectPath = "d:/kidwall/colepago-parents-app"
Set-Location $projectPath
$env:PATH = "$projectPath/tools;$env:PATH"

$outputDir = "$projectPath/build/app/outputs/flutter-apk"
$bundleOutputDir = "$projectPath/build/app/outputs/bundle"
$kidsApk = "$outputDir/app-kids-release.apk"
$parentsApk = "$outputDir/app-parents-release.apk"
$genericApk = "$outputDir/app-release.apk"
$kidsAab = "$bundleOutputDir/kidsRelease/app-kids-release.aab"
$parentsAab = "$bundleOutputDir/parentsRelease/app-parents-release.aab"
$genericAab = "$bundleOutputDir/release/app-release.aab"

if (Test-Path "$projectPath/android/gradlew.bat") {
    Push-Location "$projectPath/android"
    try {
        .\gradlew.bat --stop | Out-Host
    } finally {
        Pop-Location
    }
}

function Invoke-FlutterApkBuild {
    param(
        [Parameter(Mandatory = $true)][string]$Flavor,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$ExpectedApk
    )

    if (Test-Path $ExpectedApk) { Remove-Item $ExpectedApk -Force }
    if (Test-Path $genericApk) { Remove-Item $genericApk -Force }

    Write-Host "Building $Flavor APK..."
    flutter build apk --release --flavor $Flavor --target $Target --dart-define=FLAVOR=$Flavor
    if ($LASTEXITCODE -ne 0) {
        throw "$Flavor APK build failed with exit code $LASTEXITCODE."
    }

    if (Test-Path $ExpectedApk) {
        Write-Host "$Flavor APK generated: $ExpectedApk"
        return
    }

    if (Test-Path $genericApk) {
        Rename-Item $genericApk $ExpectedApk -Force
        Write-Host "$Flavor APK renamed to $ExpectedApk"
        return
    }

    throw "$Flavor APK build completed but expected output was not found."
}

function Invoke-FlutterAppBundleBuild {
    param(
        [Parameter(Mandatory = $true)][string]$Flavor,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$ExpectedAab
    )

    if (Test-Path $ExpectedAab) { Remove-Item $ExpectedAab -Force }
    if (Test-Path $genericAab) { Remove-Item $genericAab -Force }

    Write-Host "Building $Flavor Android App Bundle..."
    flutter build appbundle --release --flavor $Flavor --target $Target --dart-define=FLAVOR=$Flavor
    if ($LASTEXITCODE -ne 0) {
        throw "$Flavor Android App Bundle build failed with exit code $LASTEXITCODE."
    }

    if (Test-Path $ExpectedAab) {
        Write-Host "$Flavor Android App Bundle generated: $ExpectedAab"
        return
    }

    if (Test-Path $genericAab) {
        $expectedDir = Split-Path $ExpectedAab -Parent
        if (-not (Test-Path $expectedDir)) {
            New-Item -ItemType Directory -Path $expectedDir | Out-Null
        }
        Move-Item $genericAab $ExpectedAab -Force
        Write-Host "$Flavor Android App Bundle moved to $ExpectedAab"
        return
    }

    throw "$Flavor Android App Bundle build completed but expected output was not found."
}

# Build Kids APK
Invoke-FlutterApkBuild -Flavor "kids" -Target "lib/main_kid.dart" -ExpectedApk $kidsApk

# Build Kids Android App Bundle
Invoke-FlutterAppBundleBuild -Flavor "kids" -Target "lib/main_kid.dart" -ExpectedAab $kidsAab

# Build Parents APK
Invoke-FlutterApkBuild -Flavor "parents" -Target "lib/main_parent.dart" -ExpectedApk $parentsApk

# Build Parents Android App Bundle
Invoke-FlutterAppBundleBuild -Flavor "parents" -Target "lib/main_parent.dart" -ExpectedAab $parentsAab

Write-Host "Build process complete."
Write-Host "Kids APK: $kidsApk"
Write-Host "Kids AAB: $kidsAab"
Write-Host "Parents APK: $parentsApk"
Write-Host "Parents AAB: $parentsAab"
