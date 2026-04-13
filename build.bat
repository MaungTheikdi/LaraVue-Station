@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  DevStation ^— Build Script
echo  ================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Add Python to PATH and retry.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [INFO]  %%v

:: ── Install / upgrade PyInstaller ─────────────────────────────────────────────
echo [INFO]  Installing PyInstaller...
python -m pip install --quiet --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause & exit /b 1
)

:: ── Clean previous build ──────────────────────────────────────────────────────
if exist dist\DevStation.exe (
    echo [INFO]  Removing previous dist\DevStation.exe
    del /f /q dist\DevStation.exe
)
if exist build\ (
    echo [INFO]  Cleaning build\
    rmdir /s /q build
)

:: ── Build ─────────────────────────────────────────────────────────────────────
echo [INFO]  Building EXE...
pyinstaller devstation.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See output above.
    pause & exit /b 1
)

echo.
echo  ================================
echo  [OK]  dist\DevStation.exe ready
echo.
echo  Portable layout to distribute:
echo.
echo    DevStation\
echo    ^|-- DevStation.exe      ^<-- compiled EXE
echo    ^|-- bin\                ^<-- Apache / MySQL / PHP binaries
echo    ^|-- app\phpmyadmin\     ^<-- phpMyAdmin
echo    ^|-- www\                ^<-- web root
echo    ^`-- config.json         ^<-- auto-generated on first run
echo.
echo  Copy the entire folder to any Windows machine — no install needed.
echo  ================================
echo.
pause
