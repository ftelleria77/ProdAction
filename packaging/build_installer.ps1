param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$distDir = Join-Path $repoRoot "dist"
$appDist = Join-Path $distDir "ProdAction"
$installerDir = Join-Path $distDir "installer"
$specPath = Join-Path $PSScriptRoot "ProdAction.spec"
$issPath = Join-Path $PSScriptRoot "ProdAction.iss"

Write-Host "Building ProdAction executable..."
Push-Location $repoRoot
try {
    py -3 -m PyInstaller --noconfirm --clean $specPath
}
finally {
    Pop-Location
}

if (-not (Test-Path (Join-Path $appDist "ProdAction.exe"))) {
    throw "PyInstaller did not produce dist\ProdAction\ProdAction.exe"
}

$forbidden = @("docs", "archive", "tmp")
$forbiddenMatches = Get-ChildItem -Path $appDist -Directory -Recurse -Force |
    Where-Object { $forbidden -contains $_.Name }
if ($forbiddenMatches) {
    $paths = ($forbiddenMatches | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
    throw "Forbidden development folders were included:$([Environment]::NewLine)$paths"
}

if ($SkipInstaller) {
    Write-Host "Installer step skipped."
    exit 0
}

$isccCandidates = @(
    (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $isccCandidates) {
    New-Item -ItemType Directory -Force -Path $installerDir | Out-Null
    $zipPath = Join-Path $installerDir "ProdAction_portable.zip"
    if (Test-Path $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Start-Sleep -Seconds 2
    Compress-Archive -Path (Join-Path $appDist "*") -DestinationPath $zipPath
    Write-Warning "Inno Setup compiler was not found. Portable ZIP created instead: $zipPath"
    exit 0
}

Write-Host "Building installer with Inno Setup..."
& $isccCandidates $issPath

$installerPath = Join-Path $installerDir "ProdAction_Setup.exe"
if (-not (Test-Path $installerPath)) {
    throw "Installer was not produced: $installerPath"
}

Write-Host "Installer ready: $installerPath"
