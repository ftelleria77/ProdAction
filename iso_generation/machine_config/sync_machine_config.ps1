param(
    [string]$MaestroCfgx = "S:\Maestro\Cfgx",
    [string]$MaestroTlgx = "S:\Maestro\Tlgx",
    [string]$XilogPlus = "S:\Xilog Plus"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$snapshotRoot = Join-Path $scriptRoot "snapshot"
$configExtensions = @(".cfg", ".ini", ".str", ".tab", ".tlg", ".txt")
$excludedXilogFileNames = @("passwd.cfg", "rs232.cfg")

function Get-ResolvedPath {
    param([string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path
    if ($resolved.ProviderPath) {
        return $resolved.ProviderPath
    }
    return $resolved.Path
}

function Assert-PathInside {
    param(
        [string]$Path,
        [string]$Root
    )
    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    if (-not $resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside snapshot root: $resolvedPath"
    }
}

function Reset-TargetDirectory {
    param([string]$RelativePath)
    $target = Join-Path $snapshotRoot $RelativePath
    Assert-PathInside -Path $target -Root $snapshotRoot
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    return $target
}

function Copy-FullDirectory {
    param(
        [string]$Source,
        [string]$RelativeTarget
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source directory: $Source"
    }
    $target = Reset-TargetDirectory -RelativePath $RelativeTarget
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
    }
}

function Copy-SelectedXilogConfig {
    param(
        [string]$Source,
        [string]$RelativeTarget
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source directory: $Source"
    }
    $target = Reset-TargetDirectory -RelativePath $RelativeTarget
    $sourceRoot = Get-ResolvedPath -Path $Source
    $files = Get-ChildItem -LiteralPath $Source -Recurse -Force -File |
        Where-Object {
            $configExtensions -contains $_.Extension.ToLowerInvariant() -and
            $excludedXilogFileNames -notcontains $_.Name.ToLowerInvariant()
        }
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart("\", "/")
        $destination = Join-Path $target $relative
        Assert-PathInside -Path $destination -Root $snapshotRoot
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
}

function Write-Manifest {
    $manifestPath = Join-Path $snapshotRoot "manifest.csv"
    Assert-PathInside -Path $manifestPath -Root $snapshotRoot
    $rows = Get-ChildItem -LiteralPath $snapshotRoot -Recurse -Force -File |
        Where-Object { $_.FullName -ne $manifestPath } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($snapshotRoot.Length).TrimStart("\", "/").Replace("\", "/")
            $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
            [PSCustomObject]@{
                relative_path = $relative
                length = $_.Length
                last_write_time_utc = $_.LastWriteTimeUtc.ToString("o")
                sha256 = $hash.Hash.ToLowerInvariant()
            }
        }
    $rows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8
}

New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null
Copy-FullDirectory -Source $MaestroCfgx -RelativeTarget "maestro\Cfgx"
Copy-FullDirectory -Source $MaestroTlgx -RelativeTarget "maestro\Tlgx"
Copy-SelectedXilogConfig -Source $XilogPlus -RelativeTarget "xilog_plus"
Write-Manifest

Write-Output "Machine configuration snapshot updated: $snapshotRoot"
