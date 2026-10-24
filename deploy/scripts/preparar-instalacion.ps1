$ErrorActionPreference = "Stop"

$AppDirectory = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $AppDirectory ".env"
$ComposeFile = Join-Path $AppDirectory "compose.client.yml"
$ImagesFile = Join-Path $AppDirectory "images\nacagencycrm-images-1.0.0.tar"

Set-Location $AppDirectory

function New-RandomBase64Url {
    param(
        [int]$NumberOfBytes,
        [switch]$KeepPadding
    )

    $buffer = New-Object byte[] $NumberOfBytes
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()

    try {
        $generator.GetBytes($buffer)
    }
    finally {
        $generator.Dispose()
    }

    $value = [Convert]::ToBase64String($buffer)
    $value = $value.Replace("+", "-").Replace("/", "_")

    if (-not $KeepPadding) {
        $value = $value.TrimEnd("=")
    }

    return $value
}

function Get-DockerDesktopPath {
    $paths = @(
        "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe",
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $null
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop no está instalado."
}

docker info *> $null

if ($LASTEXITCODE -ne 0) {
    $dockerDesktop = Get-DockerDesktopPath

    if (-not $dockerDesktop) {
        throw "No fue posible encontrar Docker Desktop."
    }

    Write-Host "Iniciando Docker Desktop..."
    Start-Process $dockerDesktop

    $dockerReady = $false

    for ($attempt = 1; $attempt -le 60; $attempt++) {
        Start-Sleep -Seconds 3
        docker info *> $null

        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            break
        }
    }

    if (-not $dockerReady) {
        throw "Docker Desktop no respondió dentro del tiempo esperado."
    }
}

if (-not (Test-Path $EnvFile)) {
    Write-Host "Generando configuración segura..."

    $djangoSecret = New-RandomBase64Url -NumberOfBytes 64
    $jwtSecret = New-RandomBase64Url -NumberOfBytes 64
    $databasePassword = New-RandomBase64Url -NumberOfBytes 36
    $fernetKey = New-RandomBase64Url -NumberOfBytes 32 -KeepPadding

    $content = @(
        "DJANGO_SECRET_KEY=$djangoSecret"
        "JWT_SIGNING_KEY=$jwtSecret"
        "POSTGRES_DB=crm_anc"
        "POSTGRES_USER=crm_user"
        "POSTGRES_PASSWORD=$databasePassword"
        "CRM_SMTP_ENCRYPTION_KEY=$fernetKey"
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($EnvFile, $content, $encoding)
}
else {
    Write-Host "La configuración existente será conservada."
}

if (-not (Test-Path $ImagesFile)) {
    throw "No se encontró el archivo de imágenes Docker."
}

Write-Host "Importando imágenes Docker..."
docker image load -i $ImagesFile

if ($LASTEXITCODE -ne 0) {
    throw "No fue posible importar las imágenes Docker."
}

Write-Host "Validando la configuración..."
docker compose `
    --env-file $EnvFile `
    -f $ComposeFile `
    config --quiet

if ($LASTEXITCODE -ne 0) {
    throw "La configuración de Docker Compose no es válida."
}

Write-Host "Iniciando NacAgencyCRM..."
docker compose `
    --env-file $EnvFile `
    -f $ComposeFile `
    up -d --pull never

if ($LASTEXITCODE -ne 0) {
    throw "No fue posible iniciar NacAgencyCRM."
}

Write-Host ""
Write-Host "NacAgencyCRM fue instalado correctamente."