@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
title JK Draw - Update Fejlsøgning (Ingen download)

echo ============================================
echo     JK Draw - Fejlsøgningsværktøj
echo        (Downloader IKKE noget)
echo ============================================
echo.

REM --------------------------------------------
REM 1) INTERNETTEST
REM --------------------------------------------
echo [1] Tester internetforbindelse...
ping github.com -n 1 >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Ingen forbindelse til GitHub.
    goto END
) ELSE (
    echo OK: Internet virker.
)
echo.

REM --------------------------------------------
REM 2) TESTER OM GITHUB ZIP KAN NÅS (HEAD REQUEST)
REM --------------------------------------------
echo [2] Tester GitHub-adgang...
curl -I https://github.com/Jonas-Krohn0910/JK_DRAW/archive/refs/heads/main.zip >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: GitHub ZIP kan ikke tilgås.
    goto END
) ELSE (
    echo OK: GitHub ZIP kan tilgås.
)
echo.

REM --------------------------------------------
REM 3) SKRIVETEST I src/
REM --------------------------------------------
echo [3] Tester om src/ kan skrives til...
echo TEST > src\write_test.tmp 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Kan IKKE skrive til src-mappen!
    goto END
) ELSE (
    del src\write_test.tmp >nul
    echo OK: src/ er skrivbar.
)
echo.

REM --------------------------------------------
REM 4) SKRIVETEST I PROJEKTROD
REM --------------------------------------------
echo [4] Tester om projektmappen er skrivbar...
echo TEST > write_test.tmp 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Kan IKKE skrive i projektmappen!
    goto END
) ELSE (
    del write_test.tmp >nul
    echo OK: Projektmappen er skrivbar.
)
echo.

REM --------------------------------------------
REM 5) ONEDRIVE TEST
REM --------------------------------------------
echo [5] Tjekker om projektet ligger i OneDrive...
echo %cd% | find "OneDrive" >nul
IF %ERRORLEVEL% EQU 0 (
    echo ADVARSEL: Projektet ligger i OneDrive.
) ELSE (
    echo OK: Ikke i OneDrive.
)
echo.

REM --------------------------------------------
REM 6) CONTROLLED FOLDER ACCESS (failsafe)
REM --------------------------------------------
echo [6] Tjekker Windows Ransomware Protection...

powershell -command "try { (Get-MpPreference).EnableControlledFolderAccess } catch { 'UKENDT' }" > cfa.tmp 2>nul

set /p CFA=<cfa.tmp
del cfa.tmp >nul 2>&1

IF "%CFA%"=="1" (
    echo ADVARSEL: Controlled Folder Access er AKTIV.
) ELSE IF "%CFA%"=="0" (
    echo OK: Controlled Folder Access er ikke aktiv.
) ELSE (
    echo OK: Controlled Folder Access er ikke aktiv eller ukendt.
)
echo.

:END
echo ============================================
echo Fejlsøgning afsluttet.
echo Send venligst denne rapport til udvikleren.
echo ============================================
echo.
echo Tryk på en vilkårlig tast for at lukke...
pause >nul

REM --- Failsafe: hvis pause ikke blev nået ---
choice /t 99999 /d y >nul
exit /b
