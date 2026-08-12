# check_sync_reminder.ps1
# 供 Claude Code Stop hook 呼叫：
# 若「同步目的地 repo」有未 commit 的變更，在終端機顯示 sync 提醒。
#
# 目的地路徑取得順序：
#   1. 環境變數 AUTOTEST_COMPANY_REPO（建議設定，例：setx AUTOTEST_COMPANY_REPO "D:\repos\<company-repo>"）
#   2. 預設值：本 repo 的同層目錄 ..\company-repo
# 找不到目錄時直接安靜結束，不干擾其他專案。

$companyRepo = $env:AUTOTEST_COMPANY_REPO
if (-not $companyRepo) {
    $companyRepo = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "company-repo"
}

if (-not (Test-Path $companyRepo)) { exit 0 }

$repoName = Split-Path $companyRepo -Leaf
$status = git -C $companyRepo -c core.quotePath=false status --porcelain 2>$null
if ($status) {
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host " SYNC REMINDER  $repoName 有未推送的變更" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host " cd $companyRepo" -ForegroundColor Cyan
    Write-Host " git add -A && git commit -m '...' && git push origin main" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host ""
}
