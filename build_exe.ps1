# PowerShell Script for 1-click Windows EXE compilation
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Сборка Windows EXE: PDF Fingerprint & Metadata Cloner" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pyCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCheck) {
    Write-Host "[ОШИБКА] Python не обнаружен в PATH!" -ForegroundColor Red
    Write-Host "Пожалуйста, установите Python 3.10+ с https://www.python.org/" -ForegroundColor Yellow
    Write-Host "Обязательно включите галочку 'Add Python to PATH'." -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода..."
    exit 1
}

# 2. Virtual environment
Write-Host "[1/4] Подготовка виртуального окружения..." -ForegroundColor Green
if (-not (Test-Path ".venv_build")) {
    python -m venv .venv_build
}

& .venv_build\Scripts\Activate.ps1

# 3. Dependencies
Write-Host "[2/4] Установка библиотек..." -ForegroundColor Green
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. PyInstaller
Write-Host "[3/4] Компиляция автономного EXE..." -ForegroundColor Green
pyinstaller --clean PDF_Fingerprint_Cloner.spec

if ($LASTEXITCODE -eq 0 -and (Test-Path "dist\PDF_Fingerprint_Cloner.exe")) {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "   [УСПЕХ] Готовый файл создан:" -ForegroundColor Green
    Write-Host "   $(Get-Item dist\PDF_Fingerprint_Cloner.exe | Select-Object -ExpandProperty FullName)" -ForegroundColor White
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host ""
    explorer dist
} else {
    Write-Host ""
    Write-Host "[ОШИБКА] Сборка завершилась с ошибкой." -ForegroundColor Red
}

Read-Host "Нажмите Enter для выхода..."
