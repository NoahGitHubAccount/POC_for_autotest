param(
    [string]$shot = "always",
    [string]$env_name = "",       # 目標環境：dev | test | prod | local（空白 = 讀 TEST_ENV 環境變數）
    [string[]]$ExtraArgs = @()
)

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# 若傳入 -env_name 則覆寫環境變數
if ($env_name -ne "") {
    $env:TEST_ENV = $env_name
}
$currentEnv = if ($env:TEST_ENV) { $env:TEST_ENV } else { "local" }

Write-Host ""
Write-Host "================================================================"
Write-Host " Step 1/3 -- Warm Login  (env=$currentEnv)"
Write-Host "================================================================"
$env:PYTHONUTF8 = "1"
python tools/run.py --warm-login
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] warm-login failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================"
Write-Host " Step 2/3 -- Full Test Suite  (env=$currentEnv)"
Write-Host "================================================================"
$pytestArgs = @("tests/", "-v", "--tb=short", "--disable-warnings", "--shot=$shot") + $ExtraArgs
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

