# sync_to_company.ps1
#
# 職責劃分：
#   個人版控 (POC_for_autotest)  — 測試框架 + 工程經驗
#   公司版控 (aiautotest)        — 框架 + 專案產出 (tests/ specs/ input/ notes/ plan.md)
#
# 本腳本做兩件事：
#   1. 把個人版控 git 追蹤的框架檔案複製到公司 repo
#   2. 把未進個人版控的專案目錄直接複製到公司 repo
#
# 使用方式：
#   乾跑預覽     .\scripts\sync_to_company.ps1 -WhatIf
#   正式同步     .\scripts\sync_to_company.ps1
#   含刪除同步   .\scripts\sync_to_company.ps1 -SyncDeletes
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SourceDir = (Split-Path $PSScriptRoot -Parent),
    [string]$TargetDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "..\aiautotest"),
    [switch]$SyncDeletes
)

$ErrorActionPreference = "Stop"
$SourceDir = (Resolve-Path $SourceDir).Path
$TargetDir = (Resolve-Path $TargetDir).Path

Write-Host "框架來源：$SourceDir" -ForegroundColor Cyan
Write-Host "專案目標：$TargetDir" -ForegroundColor Cyan
Write-Host ""

# -------------------------------------------------------
# Part 1：框架檔案（git 追蹤清單）
# -------------------------------------------------------
Write-Host "[1/2] 同步框架檔案 (git ls-files)..." -ForegroundColor Yellow

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

$copied = 0; $skipped = 0; $failed = 0

foreach ($relPath in $trackedFiles) {
    $winRel  = $relPath -replace '/', '\'
    $srcFile = Join-Path $SourceDir $winRel
    $dstFile = Join-Path $TargetDir $winRel
    $dstDir  = Split-Path $dstFile -Parent

    if (-not (Test-Path $srcFile)) { $skipped++; continue }

    try {
        if ($PSCmdlet.ShouldProcess($dstFile, "Copy(framework)")) {
            if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force $dstDir | Out-Null }
            Copy-Item -Force $srcFile $dstFile
        }
        $copied++
    } catch {
        Write-Warning "複製失敗：$relPath — $_"; $failed++
    }
}
Write-Host "  框架：複製 $copied 筆  跳過 $skipped 筆  失敗 $failed 筆" -ForegroundColor Green

# -------------------------------------------------------
# Part 2：專案目錄（不在個人版控，直接鏡像複製）
# -------------------------------------------------------
$projectDirs = @('tests', 'specs', 'input', 'notes')
$projectFiles = @('plan.md')

Write-Host "[2/2] 同步專案目錄 ($($projectDirs -join ', '), $($projectFiles -join ', '))..." -ForegroundColor Yellow

$copied2 = 0; $failed2 = 0

foreach ($dir in $projectDirs) {
    $srcDir = Join-Path $SourceDir $dir
    $dstDir = Join-Path $TargetDir $dir
    if (-not (Test-Path $srcDir)) { continue }

    Get-ChildItem -Path $srcDir -Recurse -File | Where-Object {
        $_.FullName -notmatch '\\__pycache__\\' -and $_.Extension -ne '.pyc'
    } | ForEach-Object {
        $rel     = $_.FullName.Substring($SourceDir.Length + 1)
        $dstFile = Join-Path $TargetDir $rel
        $dstParent = Split-Path $dstFile -Parent
        try {
            if ($PSCmdlet.ShouldProcess($dstFile, "Copy(project)")) {
                if (-not (Test-Path $dstParent)) { New-Item -ItemType Directory -Force $dstParent | Out-Null }
                Copy-Item -Force $_.FullName $dstFile
            }
            $copied2++
        } catch {
            Write-Warning "複製失敗：$rel — $_"; $failed2++
        }
    }
}

foreach ($file in $projectFiles) {
    $srcFile = Join-Path $SourceDir $file
    $dstFile = Join-Path $TargetDir $file
    if (-not (Test-Path $srcFile)) { continue }
    try {
        if ($PSCmdlet.ShouldProcess($dstFile, "Copy(project)")) {
            Copy-Item -Force $srcFile $dstFile
        }
        $copied2++
    } catch {
        Write-Warning "複製失敗：$file — $_"; $failed2++
    }
}

Write-Host "  專案：複製 $copied2 筆  失敗 $failed2 筆" -ForegroundColor Green

# -------------------------------------------------------
# SyncDeletes（選用）
# -------------------------------------------------------
if ($SyncDeletes) {
    Write-Host ""
    Write-Host "[SyncDeletes] 掃描目標端多餘檔案..." -ForegroundColor Yellow

    $knownSet = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($f in $trackedFiles) { $knownSet.Add(($f -replace '/', '\').ToLower()) | Out-Null }

    foreach ($dir in $projectDirs) {
        $srcDir = Join-Path $SourceDir $dir
        if (-not (Test-Path $srcDir)) { continue }
        Get-ChildItem -Path $srcDir -Recurse -File | ForEach-Object {
            $knownSet.Add($_.FullName.Substring($SourceDir.Length + 1).ToLower()) | Out-Null
        }
    }
    foreach ($file in $projectFiles) {
        $knownSet.Add($file.ToLower()) | Out-Null
    }

    $protect = @('.git', '.venv', '.auth', 'config\config.local.yaml',
                  '__pycache__', '.pytest_cache', 'reports', 'src')
    $deleted = 0
    Get-ChildItem -Path $TargetDir -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($TargetDir.Length + 1).ToLower()
        $isProtected = $false
        foreach ($p in $protect) { if ($rel.StartsWith($p)) { $isProtected = $true; break } }
        if (-not $isProtected -and -not $knownSet.Contains($rel)) {
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
