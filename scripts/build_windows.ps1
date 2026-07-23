$ErrorActionPreference = "Stop"

$AppName = "Izbul"
$VersionFile = Join-Path $PSScriptRoot "..\VERSION"
$AppVersion = (Get-Content $VersionFile -Raw).Trim()

if ($AppVersion -notmatch '^\d+\.\d+\.\d+$') {
  throw "VERSION must use major.minor.patch format: $AppVersion"
}

$env:PYINSTALLER_CONFIG_DIR = "$PWD\build\pyinstaller-cache"
$IconPath = "$PWD\icon.ico"

py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
if (Test-Path release\windows) { Remove-Item release\windows -Recurse -Force }
New-Item -ItemType Directory -Force -Path build\spec | Out-Null
New-Item -ItemType Directory -Force -Path $env:PYINSTALLER_CONFIG_DIR | Out-Null

pyinstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name $AppName `
  --icon $IconPath `
  --add-data "$PWD\VERSION;." `
  --collect-data customtkinter `
  --collect-data PIL `
  --workpath build\work `
  --specpath build\spec `
  --distpath dist `
  ui/app.py

New-Item -ItemType Directory -Force -Path release\windows | Out-Null

$MsixStage = "$PWD\build\msix"
$MsixAssets = "$MsixStage\Assets"
$MsixPayload = "$MsixStage\$AppName"
$MsixVersion = "$AppVersion.0"
$ManifestTemplate = "$PWD\packaging\windows\AppxManifest.xml.template"
$ManifestPath = "$MsixStage\AppxManifest.xml"

New-Item -ItemType Directory -Force -Path $MsixAssets | Out-Null
New-Item -ItemType Directory -Force -Path $MsixPayload | Out-Null
Copy-Item "dist\$AppName\*" -Destination $MsixPayload -Recurse -Force

& .\venv\Scripts\python.exe scripts\generate_msix_assets.py icon.png $MsixAssets

$Manifest = (Get-Content $ManifestTemplate -Raw).Replace(
  "__MSIX_VERSION__",
  $MsixVersion
)
$Manifest | Set-Content -Path $ManifestPath -Encoding utf8

$MakeAppx = Get-Command MakeAppx.exe -ErrorAction SilentlyContinue

if (-not $MakeAppx) {
  $MakeAppx = Get-ChildItem `
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\MakeAppx.exe" `
    -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1
}

if (-not $MakeAppx) {
  throw "MakeAppx.exe was not found. Install the Windows 10/11 SDK."
}

$MakeAppxPath = if ($MakeAppx.Source) {
  $MakeAppx.Source
} else {
  $MakeAppx.FullName
}

& $MakeAppxPath pack `
  /o `
  /d $MsixStage `
  /p "release\windows\Izbul-Windows-Store.msix"

Write-Host "Created release\windows\Izbul-Windows-Store.msix"

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue

if ($iscc) {
  & $iscc.Source "/DMyAppVersion=$AppVersion" packaging\windows\izbul.iss
  Write-Host "Created release\windows\Izbul-Windows-Setup.exe"
} else {
  Compress-Archive -Path "dist\$AppName\*" -DestinationPath "release\windows\Izbul-Windows.zip" -Force
  Write-Host "Inno Setup was not found. Created release\windows\Izbul-Windows.zip instead."
}

Get-ChildItem release\windows -File |
  Where-Object { $_.Extension -in ".exe", ".zip", ".msix" } |
  ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($_.Name)" |
      Set-Content -Path "$($_.FullName).sha256" -Encoding ascii
    Write-Host "Created $($_.FullName).sha256"
  }
