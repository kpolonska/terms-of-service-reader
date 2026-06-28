@echo off
:: ToS Reader — one-click launcher for Windows
:: Double-click this file to start the backend.

cd /d "%~dp0"

:: ── 1. Check .env ─────────────────────────────────────────────────────────────
if not exist ".env" (
  powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Missing .env file.`n`nCopy .env.example to .env and add your LLMAPI_KEY, then launch again.', 'ToS Reader', 'OK', 'Error')"
  exit /b 1
)

findstr /C:"your_llmapi_key_here" .env >nul
if %errorlevel% == 0 (
  powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Please open .env and replace your_llmapi_key_here with your real LLMAPI_KEY.', 'ToS Reader', 'OK', 'Warning')"
  notepad .env
  exit /b 1
)

:: ── 2. Check Docker ───────────────────────────────────────────────────────────
docker info >nul 2>&1
if %errorlevel% neq 0 (
  powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Docker Desktop is not running.`n`nStarting Docker Desktop — wait ~30 seconds, then run start.bat again.', 'ToS Reader', 'OK', 'Information')"
  start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
  exit /b 0
)

:: ── 3. Launch ─────────────────────────────────────────────────────────────────
echo Starting ToS Reader backend...
docker compose up --build -d

if %errorlevel% neq 0 (
  powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Docker failed to start. Check docker-compose.yml and try again.', 'ToS Reader', 'OK', 'Error')"
  exit /b 1
)

powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('ToS Reader backend is running at localhost:8000' + [char]10 + [char]10 + 'You can now open website\index.html in your browser or use the Chrome extension.', 'ToS Reader', 'OK', 'Information')"
start "" "website\index.html"
