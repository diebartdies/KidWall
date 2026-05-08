param(
    [string]$Ip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw ".env file not found at $Path"
    }

    $vars = @{}
    foreach ($line in Get-Content $Path) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.TrimStart().StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }

        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        $vars[$key] = $value
    }

    return $vars
}

function Get-PublicIp {
    $sources = @(
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://checkip.amazonaws.com"
    )

    foreach ($url in $sources) {
        try {
            $result = (Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10).ToString().Trim()
            if ($result -match '^\d{1,3}(\.\d{1,3}){3}$') {
                return $result
            }
        } catch {
            continue
        }
    }

    throw "Could not resolve current public IP from known sources."
}

$envPath = Join-Path $PSScriptRoot ".env"
$cfg = Load-DotEnv -Path $envPath

$user = $cfg["EASYDNS_USER"]
$token = $cfg["EASYDNS_TOKEN"]
$hostsRaw = $cfg["EASYDNS_HOSTS"]

if ([string]::IsNullOrWhiteSpace($user)) {
    throw "EASYDNS_USER is empty in .env"
}
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "EASYDNS_TOKEN is empty in .env"
}
if ([string]::IsNullOrWhiteSpace($hostsRaw)) {
    throw "EASYDNS_HOSTS is empty in .env"
}

$hosts = $hostsRaw.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($hosts.Count -eq 0) {
    throw "No valid hosts were found in EASYDNS_HOSTS"
}

$targetIp = if ([string]::IsNullOrWhiteSpace($Ip)) { Get-PublicIp } else { $Ip.Trim() }
if ($targetIp -notmatch '^\d{1,3}(\.\d{1,3}){3}$') {
    throw "IP '$targetIp' is not a valid IPv4 address"
}

$authBytes = [System.Text.Encoding]::ASCII.GetBytes("$($user):$($token)")
$authHeader = "Basic " + [Convert]::ToBase64String($authBytes)
$headers = @{ Authorization = $authHeader }

$baseUrl = "https://api.cp.easydns.com/dyn/dyndns.php"

Write-Host "Updating EasyDNS hosts to IP $targetIp"
$hadFatalError = $false

foreach ($dnsHost in $hosts) {
    $url = "${baseUrl}?hostname=$([uri]::EscapeDataString($dnsHost))&myip=$targetIp&wildcard=NOCHG&mx=NOCHG&backmx=NOCHG"

    $response = Invoke-WebRequest -Uri $url -Headers $headers -Method Get -TimeoutSec 20
    $body = $response.Content.Trim()

    if ($body -match "^(good|nochg|NOERROR)") {
        Write-Host "OK  $dnsHost  ->  $targetIp  ($body)"
    } elseif ($body -match "^TOOSOON") {
        Write-Warning "$dnsHost rate-limited by EasyDNS (TOOSOON). Record is unchanged; retry after 600s."
    } else {
        Write-Error "EasyDNS update failed for '$dnsHost': $body"
        $hadFatalError = $true
    }
}

if ($hadFatalError) {
    throw "One or more EasyDNS records failed to update."
}

Write-Host "EasyDNS dynamic DNS update completed."
