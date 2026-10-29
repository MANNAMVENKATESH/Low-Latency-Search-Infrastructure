
# CLOUD-30 PowerShell Launcher
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BatchFile = Join-Path $ProjectRoot "start-cloud30.bat"

try {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "       CLOUD-30 PROJECT STARTER" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan

    if (-not (Test-Path $BatchFile)) {
        throw "start-cloud30.bat was not found in $ProjectRoot"
    }

    # Run the known-working batch launcher.
    # It handles frontend, Elasticsearch, and backend startup.
    Write-Host "Launching CLOUD-30..." -ForegroundColor Green

    & $env:ComSpec /c "`"$BatchFile`""

    if ($LASTEXITCODE -ne 0) {
        throw "The batch launcher exited with code $LASTEXITCODE"
    }

    Write-Host "Launcher finished." -ForegroundColor Green
}
catch {
    Write-Host "STARTUP ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
}
