$ErrorActionPreference = "Stop"

$AppName = "İzbul"
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
  --collect-data customtkinter `
  --collect-data PIL `
  --workpath build\work `
  --specpath build\spec `
  --distpath dist `
  ui/app.py

New-Item -ItemType Directory -Force -Path release\windows | Out-Null

$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue

if ($iscc) {
  & $iscc.Source packaging\windows\job-finder.iss
  Write-Host "Created release\windows\Izbul-Windows-Setup.exe"
} else {
  Compress-Archive -Path "dist\$AppName\*" -DestinationPath "release\windows\Izbul-Windows.zip" -Force
  Write-Host "Inno Setup was not found. Created release\windows\Izbul-Windows.zip instead."
}
