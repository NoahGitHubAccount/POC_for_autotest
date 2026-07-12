# nightly_run.ps1 — 夜間自動化排程主腳本
#
# 依序執行：
#   Step 1  Spec gap 偵測（WBS 缺少 spec 的工項）
#   Step 2  Test gap 偵測（spec 存在但缺少 test 的工項）
#   Step 3  Warm Login
#   Step 4  全測試套件 + 報告產出
#
# 用法：
#   .\scripts\nightly_run.ps1 -env_name test -shot on-failure
#   Task Scheduler 呼叫時加 -NonInteractive -File 完整路徑

param(
    [string]$env_name = "test",       # 目標環境：dev | test | prod | local
    [string]$shot = "on-failure"      # 截圖模式：always | on-failure | off
)

$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$env:PYTHONUTF8 = "1"
$env:TEST_ENV = $env_name

$startTime = Get-Date
$runId = $startTime.ToString("yyyyMMdd_HHmmss")
$reportDir = "$root\reports\${runId}_run"
# 讓 pytest 的 md_reporter 用同一個 run_id（否則 gap 檔與測試報告落在不同目錄，docx 步驟會撲空）
$env:MD_REPORT_RUN_ID = $runId

Write-Host ""
Write-Host "================================================================"
Write-Host " Nightly Run  env=$env_name  run_id=$runId"
Write-Host " 開始時間：$($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "================================================================"

# ── 衝突迴避：lockfile 機制 ───────────────────────────────────────────
$lockFile = "$root\.nightly.lock"
$maxRetry = 3
$retryCount = 0

while (Test-Path $lockFile) {
    $retryCount++
    if ($retryCount -ge $maxRetry) {
        Write-Host "[SKIP] lockfile 已存在（$lockFile），多次等待後仍未釋放，跳過本夜排程。" -ForegroundColor Yellow
        exit 0
    }
    Write-Host "[WARN] 偵測到 lockfile（第 $retryCount/$maxRetry 次檢查），等待 15 分鐘後重試..." -ForegroundColor Yellow
    Start-Sleep -Seconds 900
}

# 建立 lockfile（記錄 run_id）
"$runId" | Out-File $lockFile -Encoding utf8 -Force
Write-Host "[INFO] lockfile 已建立：$lockFile"

try {
    # ── Step 1：Spec gap 偵測 ─────────────────────────────────────────
    Write-Host ""
    Write-Host "── Step 1/4  Spec Gap 偵測 ──────────────────────────────────"
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    $specGap = python scripts\gen_missing_specs.py 2>&1
    $specGap | Tee-Object -FilePath "$reportDir\gap_specs.txt"

    # ── Step 2：Test gap 偵測 ─────────────────────────────────────────
    Write-Host ""
    Write-Host "── Step 2/4  Test Gap 偵測 ──────────────────────────────────"
    $testGap = python scripts\gen_missing_tests.py 2>&1
    $testGap | Tee-Object -FilePath "$reportDir\gap_tests.txt"

    # ── Step 3：Warm Login ────────────────────────────────────────────
    Write-Host ""
    Write-Host "── Step 3/4  Warm Login ─────────────────────────────────────"
    python tools\run.py --warm-login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] warm-login 失敗，中止夜間排程。" -ForegroundColor Red
        exit 1
    }

    # ── Step 4：全測試套件 ────────────────────────────────────────────
    Write-Host ""
    Write-Host "── Step 4/4  Full Test Suite ────────────────────────────────"
    & .\.venv\Scripts\pytest.exe tests/ -v --tb=short --disable-warnings --shot=$shot
    $testExitCode = $LASTEXITCODE

    # ── 產出 Word 報告 ────────────────────────────────────────────────
    Write-Host ""
    Write-Host "── 產出 Word 報告 ───────────────────────────────────────────"
    python tools\md_to_docx.py $runId

    # ── 寫入 nightly_latest.txt ───────────────────────────────────────
    $endTime = Get-Date
    $duration = ($endTime - $startTime).ToString("hh\:mm\:ss")
    $resultLabel = if ($testExitCode -eq 0) { "PASS" } else { "FAIL(exit=$testExitCode)" }
    $summaryLine = "run_id=$runId  env=$env_name  開始=$($startTime.ToString('yyyy-MM-dd HH:mm:ss'))  結束=$($endTime.ToString('HH:mm:ss'))  耗時=$duration  結果=$resultLabel"

    $summaryLine | Out-File -FilePath "$root\reports\nightly_latest.txt" -Encoding utf8 -Force
    Write-Host ""
    Write-Host "================================================================"
    Write-Host " 夜間排程完成"
    Write-Host " $summaryLine"
    Write-Host "================================================================"

    exit $testExitCode

} finally {
    # 無論成功失敗都釋放 lockfile
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    Write-Host "[INFO] lockfile 已釋放。"
}

