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
IF %ERRORLEVEL% EQU 0 (
    echo Python er allerede installeret.
    goto :check_pip
)

echo Python blev ikke fundet paa denne computer.
echo.

REM --------------------------------------------
REM 1a) FORSOEG INSTALLATION VIA WINGET
REM --------------------------------------------
where winget >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo winget blev ikke fundet paa denne computer.
    goto :curl_fallback
)

echo Installerer Python via winget ^(kraever ikke administrator-rettigheder^)...
winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Winget-installationen fejlede ^(fejlkode %ERRORLEVEL%^).
    echo Det kan skyldes manglende internetforbindelse, en firewall der
    echo blokerer winget, eller at installationen blev afbrudt.
    echo Forsoeger i stedet med en direkte download...
    goto :curl_fallback
)

echo.
echo Python er installeret via winget.
echo Luk dette vindue og koer setup.bat igen, saa Windows kan finde den
echo nye Python-installation korrekt.
pause
exit /b 0

REM --------------------------------------------
REM 1b) FALLBACK: DOWNLOAD OG INSTALLER MANUELT
REM --------------------------------------------
:curl_fallback
echo.
echo Downloader Python direkte fra python.org...
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo   Kunne ikke downloade Python
    echo ============================================
    echo Det skyldes ofte en firewall der blokerer download af .exe-filer.
    echo.
    echo Loesning: installer Python manuelt fra
    echo   https://www.python.org/downloads/
    echo og koer derefter setup.bat igen.
    pause
    exit /b 1
)

echo Installerer Python ^(kun for din egen bruger, ingen administrator
echo -rettigheder kraevet^)...
python_installer.exe InstallAllUsers=0 PrependPath=1 Include_pip=1
IF %ERRORLEVEL% NEQ 0 (
    del python_installer.exe >nul 2>&1
    echo.
    echo ============================================
    echo   Python-installationen fejlede
    echo ============================================
    echo Dette kan skyldes manglende rettigheder paa denne computer,
    echo eller at installationen blev afbrudt eller blokeret.
    echo.
    echo Loesning: installer Python manuelt fra
    echo   https://www.python.org/downloads/
    echo og koer derefter setup.bat igen.
    pause
    exit /b 1
)

del python_installer.exe >nul 2>&1

echo.
echo Python er installeret.
echo Luk dette vindue og koer setup.bat igen, saa Windows kan finde den
echo nye Python-installation korrekt.
pause
exit /b 0

REM --------------------------------------------
REM 2) TJEK OM PIP FINDES
REM --------------------------------------------
:check_pip
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Pip blev ikke fundet. Installerer pip...
    python -m ensurepip --default-pip
    IF %ERRORLEVEL% NEQ 0 (
        echo.
        echo Kunne ikke installere pip. Tjek om du har skriverettigheder
        echo til din Python-installation, eller installer Python igen.
        pause
        exit /b 1
    )
)

echo Opdaterer pip...
python -m pip install --upgrade pip
IF %ERRORLEVEL% NEQ 0 (
    echo Kunne ikke opdatere pip - fortsaetter med den nuvaerende version.
)

echo.

REM --------------------------------------------
REM 3) INSTALLER PAKKER FRA requirements.txt
REM --------------------------------------------
echo Installerer noedvendige Python-pakker...
python -m pip install -r src/requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo   Installationen af pakker fejlede
    echo ============================================
    echo Se fejlbeskeden ovenfor. De mest almindelige aarsager er:
    echo   - Manglende rettigheder ^(proev at koere denne fil som
    echo     administrator^)
    echo   - En firewall der blokerer adgang til pypi.org
    echo   - Ingen internetforbindelse
    echo.
    pause
    exit /b 1
)

echo.
echo Pakker installeret.
echo.

echo ============================================
echo   JK Draw er klar til brug
echo ============================================
echo.
echo Du kan nu starte programmet ved at koere:
echo   start.bat
echo.
pause
