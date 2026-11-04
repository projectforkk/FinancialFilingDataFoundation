param(
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @()
if ($userPath) {
    $parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() })
}

$normalizedRoot = $root.TrimEnd('\')

if ($Remove) {
    $newParts = @($parts | Where-Object {
        $_.TrimEnd('\') -ne $normalizedRoot
    })
    [Environment]::SetEnvironmentVariable('Path', ($newParts -join ';'), 'User')
    Write-Host "Removed FFDF project root from User PATH:"
    Write-Host "  $root"
    Write-Host "Open a new PowerShell window before testing."
    exit 0
}

if (-not (Test-Path (Join-Path $root 'ffdf.cmd'))) {
    throw "ffdf.cmd not found under project root: $root"
}

$alreadyPresent = $false
foreach ($part in $parts) {
    if ($part.TrimEnd('\') -eq $normalizedRoot) {
        $alreadyPresent = $true
        break
    }
}

if (-not $alreadyPresent) {
    $newPath = if ($userPath) { "$userPath;$root" } else { $root }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Write-Host "Added FFDF project root to User PATH:"
    Write-Host "  $root"
} else {
    Write-Host "FFDF project root is already in User PATH:"
    Write-Host "  $root"
}

Write-Host ""
Write-Host "Open a new PowerShell window, then run:"
Write-Host "  ffdf --help"
Write-Host "  ffdf acquire --market CN --ticker 600519 --year 2026 --period Q3"
Write-Host "  ffdf ingest  --market CN --ticker 600519 --year 2026 --period Q3"
