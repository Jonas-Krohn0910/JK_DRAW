@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
title JK Draw - Installations Fejlsøgning (Ingen installation)

echo ============================================
echo     JK Draw - Installations Fejlsøgning
echo        (Udfører INGEN installation)
echo ============================================
echo.

REM --------------------------------------------
REM 1) TJEK PYTHON
REM --------------------------------------------
echo [1] Tester Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Python er IKKE installeret eller ikke i PATH.
) ELSE (
    for /f "delims=" %%i in ('python --version') do echo OK: %%i
)
echo.

REM --------------------------------------------
REM 2) TJEK PIP (Windows-sikker metode)
REM --------------------------------------------
echo [2] Tester pip...

python -c "import pip" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: pip er IKKE installeret eller virker ikke.
) ELSE (
    python -m pip --version
)
echo.

REM --------------------------------------------
REM 3) TJEK requirements.txt
REM --------------------------------------------
echo [3] Tester om src\requirements.txt findes...
IF NOT EXIST src\requirements.txt (
    echo FEJL: src\requirements.txt findes IKKE.
) ELSE (
    echo OK: Filen findes.
    echo Tester om filen kan læses...
    type src\requirements.txt >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo FEJL: Filen kan IKKE læses.
    ) ELSE (
        echo OK: Filen kan læses.
    )
)
echo.

REM --------------------------------------------
REM 4) SKRIVETEST I src/
REM --------------------------------------------
echo [4] Tester om src/ kan skrives til...
echo TEST > src\write_test.tmp 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Kan IKKE skrive til src-mappen!
) ELSE (
    del src\write_test.tmp >nul
    echo OK: src/ er skrivbar.
)
echo.

REM --------------------------------------------
REM 5) SKRIVETEST I PROJEKTROD
REM --------------------------------------------
echo [5] Tester om projektmappen er skrivbar...
echo TEST > write_test.tmp 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo FEJL: Kan IKKE skrive i projektmappen!
) ELSE (
    del write_test.tmp >nul
    echo OK: Projektmappen er skrivbar.
)
echo.

REM --------------------------------------------
REM 6) ONEDRIVE TEST
REM --------------------------------------------
echo [6] Tjekker om projektet ligger i OneDrive...
echo %cd% | find "OneDrive" >nul
IF %ERRORLEVEL% EQU 0 (
    echo ADVARSEL: Projektet ligger i OneDrive.
) ELSE (
    echo OK: Ikke i OneDrive.
)
echo.

REM --------------------------------------------
REM 7) CONTROLLED FOLDER ACCESS
REM --------------------------------------------
echo [7] Tjekker Windows Ransomware Protection...

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

echo ============================================
echo Fejlsøgning afsluttet.
echo Send venligst denne rapport til udvikleren.
echo ============================================
echo.
echo Tryk på en vilkårlig tast for at lukke...
pause >nul

choice /t 99999 /d y >nul
exit /b
