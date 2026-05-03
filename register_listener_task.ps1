# Run this script ONCE as Administrator to register the speech listener
# as a Scheduled Task that starts automatically when you log in.

$TaskName    = "SpeechListenerAutoStart"
$BatFile     = "D:\kidwall\start_listener.bat"
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Remove old task if it exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Define the action: run the bat file hidden (no console window)
$Action  = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatFile`""

# Trigger: at logon of current user
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser

# Settings: allow running indefinitely, restart on failure
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# Run as the current logged-in user (so microphone works)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Always-on speech-to-text listener (Whisper + SoX)" `
    -Force

Write-Host ""
Write-Host "Task '$TaskName' registered successfully." -ForegroundColor Green
Write-Host "It will start automatically the next time you log in." -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Start now:  Start-ScheduledTask  -TaskName '$TaskName'"
Write-Host "  Stop:       Stop-ScheduledTask   -TaskName '$TaskName'"
Write-Host "  Remove:     Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
