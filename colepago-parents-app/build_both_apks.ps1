# PowerShell script to build both kids and parents APKs using Flutter flavors
$ErrorActionPreference = "Stop"

$projectPath = "d:/kidwall/colepago-parents-app"
Set-Location $projectPath

$outputDir = "$projectPath/build/app/outputs/flutter-apk"
$kidsApk = "$outputDir/app-kids-release.apk"
$parentsApk = "$outputDir/app-parents-release.apk"
$genericApk = "$outputDir/app-release.apk"

if (Test-Path "$projectPath/android/gradlew.bat") {
    Push-Location "$projectPath/android"
    try {
        .\gradlew.bat --stop | Out-Host
    } finally {
        Pop-Location
    }
}

function Invoke-FlutterBuild {
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

# Build Kids APK
Invoke-FlutterBuild -Flavor "kids" -Target "lib/main_kid.dart" -ExpectedApk $kidsApk

# Build Parents APK
Invoke-FlutterBuild -Flavor "parents" -Target "lib/main_parent.dart" -ExpectedApk $parentsApk

Write-Host "Build process complete."
Write-Host "Kids APK: $kidsApk"
Write-Host "Parents APK: $parentsApk"
