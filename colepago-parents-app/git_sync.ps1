# PowerShell script to automate git add, commit, and push for the project

$projectPath = "d:/kidwall/colepago-parents-app"
Set-Location $projectPath

# Show git status
Write-Host "--- GIT STATUS ---"
git status

# Stage all changes
Write-Host "--- GIT ADD ---"
git add .

# Commit with timestamp
$commitMsg = "Auto-sync: flavors, scripts, and UI $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "--- GIT COMMIT ---"
git commit -m "$commitMsg"

# Push to remote
Write-Host "--- GIT PUSH ---"
git push

Write-Host "--- SYNC COMPLETE ---"
