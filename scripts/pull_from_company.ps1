# pull_from_company.ps1
#
# From: company repo (<company-repo>) -> this repo (local)
# Conflict: framework files dirty in both repos -> report only, no auto-overwrite
# Safe copy: tests/ specs/ plan.md (not tracked locally) + framework only dirty in company
#
# Company repo path resolution: -CompanyDir > $env:AUTOTEST_COMPANY_REPO > ..\company-repo
#
# Usage:
#   dry-run:  .\scripts\pull_from_company.ps1 -WhatIf
#   run:      .\scripts\pull_from_company.ps1
#   custom:   .\scripts\pull_from_company.ps1 -CompanyDir D:\repos\<company-repo>
#   skip pull:.\scripts\pull_from_company.ps1 -SkipPull
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$LocalDir   = (Split-Path $PSScriptRoot -Parent),
    [string]$CompanyDir = $(if ($env:AUTOTEST_COMPANY_REPO) { $env:AUTOTEST_COMPANY_REPO }
                            else { Join-Path (Split-Path $PSScriptRoot -Parent) "..\company-repo" }),
    [switch]$SkipPull
)

$ErrorActionPreference = "Stop"
$LocalDir   = (Resolve-Path $LocalDir).Path
$CompanyDir = (Resolve-Path $CompanyDir).Path

Write-Host "Local  : $LocalDir"   -ForegroundColor Cyan
Write-Host "Company: $CompanyDir" -ForegroundColor Cyan
Write-Host ""

# -------------------------------------------------------
# Step 1: git pull (company repo)
# -------------------------------------------------------
if (-not $SkipPull) {
    Write-Host "[1/3] git pull (company repo)..." -ForegroundColor Yellow
    Push-Location $CompanyDir
    try {
        git pull
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARN] git pull failed (exit $LASTEXITCODE). Continuing with local state." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARN] git pull error: $_. Continuing with local state." -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
    Write-Host ""
} else {
    Write-Host "[1/3] Skipping git pull (-SkipPull)" -ForegroundColor DarkGray
}

# -------------------------------------------------------
# Step 2: Detect conflicts
# -------------------------------------------------------
Write-Host "[2/3] Detecting conflicts..." -ForegroundColor Yellow

function Get-DirtyFiles {
    param([string]$RepoDir)
    Push-Location $RepoDir
    try {
        # Use cmd /c to suppress git's stderr warnings in PowerShell 5.1
        $out = cmd /c "git diff HEAD --name-only 2>nul"
        if ($null -eq $out) { return @() }
        return @($out | ForEach-Object { ($_.Trim()) -replace '/', '\' } | Where-Object { $_ -ne '' })
    } finally {
        Pop-Location
    }
}

$localDirty   = Get-DirtyFiles -RepoDir $LocalDir
$companyDirty = Get-DirtyFiles -RepoDir $CompanyDir

$frameworkPrefixes = @('lib\','docs\','prompts\','config\','scripts\','tools\','conftest.py','pytest.ini','requirements.txt')

$conflicts  = [System.Collections.Generic.List[string]]::new()
$safeToCopy = [System.Collections.Generic.List[string]]::new()

foreach ($cf in $companyDirty) {
    $isFramework = $false
    foreach ($p in $frameworkPrefixes) {
        if ($cf.StartsWith($p) -or $cf -eq $p) { $isFramework = $true; break }
    }
    if (-not $isFramework) { continue }
    if ($localDirty -contains $cf) {
        $conflicts.Add($cf)
    } else {
        $safeToCopy.Add($cf)
    }
}

# Report
if ($conflicts.Count -gt 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "  CONFLICT: Both sides modified - NOT auto-copied" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    foreach ($f in $conflicts) {
        Write-Host "  [CONFLICT] $f" -ForegroundColor Red
        Write-Host "    company: $CompanyDir\$f"
        Write-Host "    local  : $LocalDir\$f"
    }
    Write-Host ""
}

if ($safeToCopy.Count -gt 0) {
    Write-Host "Framework files to auto-copy (only company changed):" -ForegroundColor Green
    foreach ($f in $safeToCopy) {
        Write-Host "  [COPY] $f" -ForegroundColor Green
    }
    Write-Host ""
}

# -------------------------------------------------------
# Step 3: Copy files
# -------------------------------------------------------
Write-Host "[3/3] Syncing files..." -ForegroundColor Yellow

$copied  = 0
$skipped = 0

# 3-A: Safe framework files
foreach ($f in $safeToCopy) {
    $src    = Join-Path $CompanyDir $f
    $dst    = Join-Path $LocalDir   $f
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $src)) { $skipped++; continue }
    if ($PSCmdlet.ShouldProcess($dst, "Copy framework")) {
        if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force $dstDir | Out-Null }
        Copy-Item -Force $src $dst
        $copied++
    }
}

# 3-B: tests/ specs/ plan.md (not tracked locally, always overwrite)
$projectItems = @('tests', 'specs', 'plan.md')
foreach ($item in $projectItems) {
    $src = Join-Path $CompanyDir $item
    $dst = Join-Path $LocalDir   $item
    if (-not (Test-Path $src)) { $skipped++; continue }

    if (Test-Path $src -PathType Container) {
        $files = Get-ChildItem -Path $src -Recurse -File |
            Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and $_.Extension -ne '.pyc' }
        foreach ($file in $files) {
            $rel       = $file.FullName.Substring($src.Length)
            $dstFile   = Join-Path $dst $rel
            $dstParent = Split-Path $dstFile -Parent
            if ($PSCmdlet.ShouldProcess($dstFile, "Copy project")) {
                if (-not (Test-Path $dstParent)) { New-Item -ItemType Directory -Force $dstParent | Out-Null }
                Copy-Item -Force $file.FullName $dstFile
                $copied++
            }
        }
    } else {
        $dstParent = Split-Path $dst -Parent
        if ($PSCmdlet.ShouldProcess($dst, "Copy project")) {
            if (-not (Test-Path $dstParent)) { New-Item -ItemType Directory -Force $dstParent | Out-Null }
            Copy-Item -Force $src $dst
            $copied++
        }
    }
}

Write-Host "  Copied: $copied  Skipped: $skipped" -ForegroundColor Green
Write-Host ""

# -------------------------------------------------------
# Final summary
# -------------------------------------------------------
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($conflicts.Count -gt 0) {
    Write-Host "[!] Files requiring manual merge:" -ForegroundColor Red
    foreach ($f in $conflicts) {
        Write-Host "    $f" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "To compare:" -ForegroundColor Yellow
    foreach ($f in $conflicts) {
        Write-Host "    code --diff `"$CompanyDir\$f`" `"$LocalDir\$f`"" -ForegroundColor White
    }
} else {
    Write-Host "[OK] No conflicts. All framework changes merged automatically." -ForegroundColor Green
}

Write-Host "tests/ specs/ plan.md synced from company repo." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
