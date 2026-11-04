@echo off
chcp 65001 > nul
title Сборка PDF Fingerprint Cloner в EXE

echo ========================================================
echo    Сборка Windows EXE: PDF Fingerprint ^& Metadata Cloner
echo ========================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден в системе!
    echo Установите Python 3.10+ с сайта python.org и отметьте галочку "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

echo [1/4] Создание виртуального окружения...
if not exist ".venv_build" (
    python -m venv .venv_build
)

call .venv_build\Scripts\activate.bat

echo [2/4] Обновление pip и установка зависимостей...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Компиляция в один автономный .exe файл через PyInstaller...
pyinstaller --clean PDF_Fingerprint_Cloner.spec

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Произошла ошибка при сборке EXE!
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   [УСПЕХ] Сборка завершена успешно!
echo   Готовый файл: dist\PDF_Fingerprint_Cloner.exe
echo ========================================================
echo.

REM Открываем папку с готовым EXE
explorer dist

pause
