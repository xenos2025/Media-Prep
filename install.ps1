# Install the media-prep-workbench Agent Skill into a Cursor skills directory
# (user global by default) or a project.
# Usage:
#   ./install.ps1
#   ./install.ps1 -Project .
#   ./install.ps1 -Dest "$HOME\.cursor\skills\media-prep-workbench"
#   ./install.ps1 -Force

param(
    [string]$Dest = "",
    [string]$Project = "",
    [string[]]$Skills = @("media-prep-workbench"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Assert-SafeTarget {
    param(
        [string]$Path,
        [string]$SkillName
    )

    $Full = [System.IO.Path]::GetFullPath($Path)
    $Comparable = $Full.TrimEnd([char[]]@('\', '/'))
    $RootPath = [System.IO.Path]::GetPathRoot($Full).TrimEnd([char[]]@('\', '/'))
    $HomePath = [System.IO.Path]::GetFullPath($HOME).TrimEnd([char[]]@('\', '/'))
    $RepoPath = [System.IO.Path]::GetFullPath($Root).TrimEnd([char[]]@('\', '/'))
    $ParentPath = [System.IO.Path]::GetFullPath((Split-Path -Parent $Full)).TrimEnd([char[]]@('\', '/'))

    foreach ($Blocked in @($RootPath, $HomePath, $RepoPath)) {
        if ($Comparable.Equals($Blocked, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe install target: $Full"
        }
    }
    if ($ParentPath.Equals($RootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to install directly under a drive root: $Full"
    }
    if ((Split-Path -Leaf $Comparable) -ne $SkillName) {
        throw "Install target must end with the skill name '$SkillName': $Full"
    }
    return $Full
}

if ($Dest -ne "") {
    $Skills = @($Skills[0])
}

if ($Dest -eq "" -and $Project -ne "") {
    $Base = Join-Path (Resolve-Path $Project) ".cursor\skills"
}
elseif ($Dest -eq "") {
    $Base = Join-Path $HOME ".cursor\skills"
}

foreach ($Skill in $Skills) {
    $Src = Join-Path $Root "skill\$Skill"
    if (-not (Test-Path $Src)) {
        throw "Missing skill/$Skill at $Src"
    }

    $Target = if ($Dest -ne "") { $Dest } else { Join-Path $Base $Skill }
    $Target = Assert-SafeTarget -Path $Target -SkillName $Skill

    $TargetParent = Split-Path -Parent $Target
    New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null

    if ((Test-Path $Target) -and -not $Force) {
        throw "Destination exists: $Target (pass -Force to overwrite)"
    }

    if (Test-Path $Target) {
        Remove-Item -Recurse -Force $Target
    }

    Copy-Item -Recurse $Src $Target
    Write-Host "Installed $Skill -> $Target"
}

Write-Host "Requires Python 3.10+, Pillow, and FFmpeg on PATH for video. Try:"
Write-Host "  python -m pip install -e `"$Root`""
Write-Host "  python -m media_prep inspect-images --src path\to\images --out path\to\out\inspect-images"
Write-Host "  python `"$HOME\.cursor\skills\media-prep-workbench\scripts\media_prep.py`" -h"
