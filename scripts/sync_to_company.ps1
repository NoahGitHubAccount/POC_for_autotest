# sync_to_company.ps1
# 將 POC_for_autotest (個人版控) 的 git 追蹤檔案同步到 aiautotest (公司版控)
#
# 使用方式：
#   乾跑預覽          .\scripts\sync_to_company.ps1 -WhatIf
#   正式同步          .\scripts\sync_to_company.ps1
#   含刪除同步        .\scripts\sync_to_company.ps1 -SyncDeletes
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SourceDir = (Split-Path $PSScriptRoot -Parent),
    [string]$TargetDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "..\aiautotest"),
    [switch]$SyncDeletes
)

$ErrorActionPreference = "Stop"
$SourceDir = (Resolve-Path $SourceDir).Path
$TargetDir = (Resolve-Path $TargetDir).Path

Write-Host "來源：$SourceDir" -ForegroundColor Cyan
Write-Host "目標：$TargetDir" -ForegroundColor Cyan
Write-Host ""

Push-Location $SourceDir
try {
    $trackedFiles = git -c core.quotePath=false ls-files | ForEach-Object { $_.Trim() }
} finally {
    Pop-Location
}

if (-not $trackedFiles) {
    Write-Error "git ls-files 回傳空結果"
    exit 1
}

$copied  = 0
$skipped = 0
$failed  = 0

foreach ($relPath in $trackedFiles) {
    $winRel = $relPath -replace '/', '\'
    $srcFile = Join-Path $SourceDir $winRel
    $dstFile = Join-Path $TargetDir $winRel
    $dstDir  = Split-Path $dstFile -Parent

    if (-not (Test-Path $srcFile)) {
        Write-Warning "來源不存在（跳過）：$relPath"
        $skipped++
        continue
    }

    try {
        if ($PSCmdlet.ShouldProcess($dstFile, "Copy")) {
            if (-not (Test-Path $dstDir)) {
                New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
            }
            Copy-Item -Force -Path $srcFile -Destination $dstFile
        }
        $copied++
    } catch {
        Write-Warning "複製失敗：$relPath — $_"
        $failed++
    }
}

Write-Host ""
Write-Host "複製：$copied 筆  跳過：$skipped 筆  失敗：$failed 筆" -ForegroundColor Green

if ($SyncDeletes) {
    Write-Host ""
    Write-Host "[SyncDeletes] 掃描目標端多餘檔案..." -ForegroundColor Yellow

    $trackedSet = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($f in $trackedFiles) {
        $trackedSet.Add(($f -replace '/', '\').ToLower()) | Out-Null
    }

    $protect = @('.git', '.venv', '.auth', 'config\config.local.yaml',
                  '__pycache__', '.pytest_cache', 'reports', 'src')

    $deleted = 0
    Get-ChildItem -Path $TargetDir -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($TargetDir.Length + 1).ToLower()
        $isProtected = $false
        foreach ($p in $protect) {
            if ($rel.StartsWith($p)) { $isProtected = $true; break }
        }
        if (-not $isProtected -and -not $trackedSet.Contains($rel)) {
            if ($PSCmdlet.ShouldProcess($_.FullName, "Delete")) {
                Remove-Item -Force $_.FullName
                Write-Host "  已刪除：$rel" -ForegroundColor DarkYellow
            }
            $deleted++
        }
    }
    Write-Host "刪除：$deleted 筆" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "同步完成。請進入 $TargetDir 執行 git status 後推送。" -ForegroundColor Green
