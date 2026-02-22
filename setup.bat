@echo off
title Installerer JK Draw

echo ============================================
echo        JK Draw - Windows Setup
echo ============================================
echo.

REM --------------------------------------------
REM 1) TJEK OM PYTHON ER INSTALLERET
REM --------------------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python ikke fundet.
    echo Downloader Python 3.12...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe

    echo Installerer Python...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

    echo Python installeret. Genstarter installationsprogrammet...
    start "" "%~f0"
    exit /b
) ELSE (
    echo Python er allerede installeret.
)

echo.

REM --------------------------------------------
REM 2) TJEK OM PIP FINDES
REM --------------------------------------------
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Pip ikke fundet. Installerer pip...
    python -m ensurepip --default-pip
)

echo Opdaterer pip...
python -m pip install --upgrade pip

echo.

REM --------------------------------------------
REM 3) INSTALLER PAKKER FRA requirements.txt
REM --------------------------------------------
echo Installerer nødvendige Python-pakker...

python -m pip install -r src/requirements.txt

echo.
echo Pakker installeret.
echo.

echo ============================================
echo   JK Draw er klar til brug
echo ============================================
echo.
echo Du kan nu starte programmet ved at køre:
echo   start.bat
echo.
pause
