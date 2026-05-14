# check_sync_reminder.ps1
# 供 Claude Code Stop hook 呼叫：
# 若 aiautotest 有未 commit 的變更，在終端機顯示 sync 提醒。
$aiAutotest = "D:\daily-records\專案\FOXCONN\aiautotest"

if (-not (Test-Path $aiAutotest)) { exit 0 }

$status = git -C $aiAutotest -c core.quotePath=false status --porcelain 2>$null
if ($status) {
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host " SYNC REMINDER  aiautotest 有未推送的變更" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host " cd D:\daily-records\專案\FOXCONN\aiautotest" -ForegroundColor Cyan
    Write-Host " git add -A && git commit -m '...' && git push origin main" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host ""
}
