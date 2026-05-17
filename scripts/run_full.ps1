param(
    [string]$shot = "always",
    [string[]]$ExtraArgs = @()
)

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host ""
Write-Host "================================================================"
Write-Host " Step 1/3 -- Warm Login"
Write-Host "================================================================"
python tools/run.py --warm-login
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] warm-login failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================"
Write-Host " Step 2/3 -- Full Test Suite"
Write-Host "================================================================"
$env:PYTHONUTF8 = "1"
$pytestArgs = @("tests/", "-v", "--shot=$shot") + $ExtraArgs
& .\.venv\Scripts\pytest.exe @pytestArgs
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================"
Write-Host " Step 3/3 -- Done"
Write-Host "================================================================"
$latestRun = Get-ChildItem "$root\reports" -Directory -Filter "*_run" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty Name

if ($latestRun) {
    $runId = $latestRun -replace "_run$", ""
    Write-Host "run_id: $runId"
    Write-Host "Word report: python tools/md_to_docx.py $runId"
}

exit $exitCode
