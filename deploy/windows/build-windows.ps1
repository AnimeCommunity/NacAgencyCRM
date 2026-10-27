param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FrontendRoot = Join-Path $RepoRoot "frontendcrm"
$BackendRoot = Join-Path $RepoRoot "CRM"
$BuildRoot = Join-Path $RepoRoot ".build\windows"
$VenvRoot = Join-Path $BuildRoot "venv"
$Python = Join-Path $VenvRoot "Scripts\python.exe"
$SpecFile = Join-Path $PSScriptRoot "NacAgencyCRM.spec"
$DistRoot = Join-Path $RepoRoot "dist\windows"
$WorkRoot = Join-Path $BuildRoot "pyinstaller"
$ExpectedPython = "3.11.5"
$ExpectedNode = "v26.7.0"
$ExpectedNpm = "11.19.0"
$ApplicationVersion = (Get-Content (Join-Path $PSScriptRoot "version.txt") -Raw).Trim()
$VersionInfoContent = Get-Content (Join-Path $PSScriptRoot "version-info.txt") -Raw
$VersionParts = $ApplicationVersion.Split('.')
if ($VersionParts.Count -ne 3) { throw "La versión debe tener el formato mayor.menor.parche." }
$NumericVersion = "$($VersionParts[0]), $($VersionParts[1]), $($VersionParts[2]), 0"
$ExpectedVersionEntries = @(
    "filevers=($NumericVersion)",
    "prodvers=($NumericVersion)",
    "StringStruct('FileVersion', '$ApplicationVersion')",
    "StringStruct('ProductVersion', '$ApplicationVersion')"
)
if ($ExpectedVersionEntries | Where-Object { $VersionInfoContent -notmatch [regex]::Escape($_) }) {
    throw "version-info.txt no coincide con version.txt ($ApplicationVersion)."
}

$ActualPython = (& py -3.11 -c "import platform; print(platform.python_version())").Trim()
$ActualNode = (& node --version).Trim()
$ActualNpm = (& npm --version).Trim()
if ($ActualPython -ne $ExpectedPython) { throw "Se requiere Python $ExpectedPython; se encontró $ActualPython." }
if ($ActualNode -ne $ExpectedNode) { throw "Se requiere Node.js $ExpectedNode; se encontró $ActualNode." }
if ($ActualNpm -ne $ExpectedNpm) { throw "Se requiere npm $ExpectedNpm; se encontró $ActualNpm." }

Write-Host "[1/5] Construyendo frontend estático..."
$SavedNextPublicEnvironment = @{}
Get-ChildItem Env: | Where-Object { $_.Name -like "NEXT_PUBLIC_*" } | ForEach-Object {
    $SavedNextPublicEnvironment[$_.Name] = $_.Value
    Remove-Item ("Env:" + $_.Name)
}
$env:NEXT_PUBLIC_API_URL = "/api"
Push-Location $FrontendRoot
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "npm ci falló." }
    npm test
    if ($LASTEXITCODE -ne 0) { throw "Las pruebas del frontend fallaron." }
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "El lint del frontend falló." }
    npx tsc --noEmit
    if ($LASTEXITCODE -ne 0) { throw "La verificación TypeScript del frontend falló." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "El build del frontend falló." }
    npm audit --audit-level=high
    if ($LASTEXITCODE -ne 0) { throw "La auditoría de dependencias del frontend falló." }
}
finally {
    Pop-Location
    Remove-Item Env:NEXT_PUBLIC_API_URL -ErrorAction SilentlyContinue
    foreach ($Name in $SavedNextPublicEnvironment.Keys) {
        Set-Item -Path ("Env:" + $Name) -Value $SavedNextPublicEnvironment[$Name]
    }
}

Write-Host "[2/5] Preparando Python 3.11..."
if (Test-Path $VenvRoot) { Remove-Item $VenvRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
py -3.11 -m venv $VenvRoot
if ($LASTEXITCODE -ne 0) { throw "No fue posible crear el entorno Python 3.11." }

& $Python -m pip install --no-deps -r (Join-Path $BackendRoot "requirements-windows.lock.txt")
if ($LASTEXITCODE -ne 0) { throw "No fue posible instalar las dependencias de Windows." }

if (-not $SkipTests) {
    Write-Host "[3/5] Ejecutando pruebas backend con SQLite..."
    $PreviousDbEngine = $env:DB_ENGINE
    $PreviousSqliteName = $env:SQLITE_NAME
    $PreviousEnvironment = $env:DJANGO_ENV
    try {
        $env:DB_ENGINE = "sqlite"
        $env:SQLITE_NAME = Join-Path $BuildRoot "tests.sqlite3"
        $env:DJANGO_ENV = "development"
        Push-Location $BackendRoot
        try {
            & $Python manage.py test -v 1
            if ($LASTEXITCODE -ne 0) { throw "Las pruebas backend fallaron." }
            & $Python manage.py makemigrations --check --dry-run
            if ($LASTEXITCODE -ne 0) { throw "Se detectaron cambios de modelos sin migración." }
            & $Python manage.py check
            if ($LASTEXITCODE -ne 0) { throw "La verificación de Django falló." }
            & $Python -m pip check
            if ($LASTEXITCODE -ne 0) { throw "La verificación de dependencias Python falló." }
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:DB_ENGINE = $PreviousDbEngine
        $env:SQLITE_NAME = $PreviousSqliteName
        $env:DJANGO_ENV = $PreviousEnvironment
    }
}
else {
    Write-Host "[3/5] Pruebas omitidas por parámetro."
}

Write-Host "[4/5] Empaquetando aplicación Windows..."
if (Test-Path $DistRoot) { Remove-Item $DistRoot -Recurse -Force }
if (Test-Path $WorkRoot) { Remove-Item $WorkRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null

$PreviousDbEngine = $env:DB_ENGINE
$PreviousSqliteName = $env:SQLITE_NAME
$PreviousEnvironment = $env:DJANGO_ENV
$PreviousPath = $env:PATH
try {
    $env:DB_ENGINE = "sqlite"
    $env:SQLITE_NAME = Join-Path $BuildRoot "package-do-not-include.sqlite3"
    $env:DJANGO_ENV = "development"
    $env:PATH = (($env:PATH -split ';') | Where-Object { $_ -notmatch '(?i)[\\/]jdk|[\\/]java[\\/]' }) -join ';'
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $DistRoot `
        --workpath $WorkRoot `
        $SpecFile
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller no pudo generar la aplicación." }
}
finally {
    $env:PATH = $PreviousPath
    $env:DB_ENGINE = $PreviousDbEngine
    $env:SQLITE_NAME = $PreviousSqliteName
    $env:DJANGO_ENV = $PreviousEnvironment
}

$AnalysisFile = Join-Path $WorkRoot "NacAgencyCRM\Analysis-00.toc"
if ((Test-Path $AnalysisFile) -and (Select-String -Path $AnalysisFile -Pattern '(?i)[\\/]jdk|[\\/]java[\\/]' -Quiet)) {
    throw "PyInstaller incorporó binarios desde una instalación Java/JDK no declarada."
}

$ForbiddenFiles = Get-ChildItem (Join-Path $DistRoot "NacAgencyCRM") -Recurse -File |
    Where-Object {
        $Name = $_.Name.ToLowerInvariant()
        $Name -eq "secrets.json" -or
        $Name.StartsWith(".env") -or
        $Name -in @("id_rsa", "id_ed25519") -or
        $_.Extension.ToLowerInvariant() -in @(
            ".sqlite", ".sqlite3", ".db", ".pem", ".key", ".pfx", ".p12"
        )
    }
if ($ForbiddenFiles) {
    $Names = ($ForbiddenFiles | ForEach-Object { $_.FullName }) -join ", "
    throw "El paquete contiene datos o secretos prohibidos: $Names"
}

$SmokeRoot = Join-Path $BuildRoot "smoke-data"
if (Test-Path $SmokeRoot) { Remove-Item $SmokeRoot -Recurse -Force }
$PackagedExe = Join-Path $DistRoot "NacAgencyCRM\NacAgencyCRM.exe"
& $PackagedExe --validate-bundle --data-root $SmokeRoot
if ($LASTEXITCODE -ne 0) { throw "La verificación del ejecutable empaquetado falló." }
& $PackagedExe --backup --data-root $SmokeRoot
if ($LASTEXITCODE -ne 0) { throw "El respaldo del ejecutable empaquetado falló." }
if (-not (Get-ChildItem (Join-Path $SmokeRoot "backups") -Filter "*.zip" -File)) {
    throw "El ejecutable empaquetado no generó el respaldo esperado."
}

Write-Host "[5/5] Aplicación generada en:"
Write-Host (Join-Path $DistRoot "NacAgencyCRM\NacAgencyCRM.exe")
