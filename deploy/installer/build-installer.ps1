param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ApplicationExe = Join-Path $RepoRoot "dist\windows\NacAgencyCRM\NacAgencyCRM.exe"
$InstallerScript = Join-Path $PSScriptRoot "NacAgencyCRM.iss"
$Version = (Get-Content (Join-Path $RepoRoot "deploy\windows\version.txt") -Raw).Trim()
$CompilerCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Compiler = $CompilerCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not (Test-Path $ApplicationExe)) {
    throw "No existe el paquete de aplicación. Ejecute primero deploy\windows\build-windows.ps1."
}
$ApplicationBuildTime = (Get-Item $ApplicationExe).LastWriteTimeUtc
$SourceFiles = @(
    Get-ChildItem (Join-Path $RepoRoot "CRM") -Recurse -File
    Get-ChildItem (Join-Path $RepoRoot "frontendcrm") -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/](node_modules|\.next|out)[\\/]' }
    Get-ChildItem (Join-Path $RepoRoot "deploy\windows") -Recurse -File
)
$NewerSource = $SourceFiles |
    Where-Object { $_.LastWriteTimeUtc -gt $ApplicationBuildTime } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
if ($NewerSource) {
    throw "El paquete está desactualizado respecto a $($NewerSource.FullName). Reconstruya la aplicación antes del instalador."
}
if (-not $Compiler) {
    throw "Inno Setup 6 no está instalado. Instálelo con: winget install --id JRSoftware.InnoSetup --exact"
}

& $Compiler "/DMyAppVersion=$Version" $InstallerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup no pudo generar el instalador."
}

Write-Host "Instalador generado en:"
Write-Host (Join-Path $PSScriptRoot "Output\NacAgencyCRM-Setup-$Version.exe")
