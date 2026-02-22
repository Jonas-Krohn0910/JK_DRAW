@echo off
title JK Draw

REM Skift til mappen hvor start.bat ligger
cd /d "%~dp0"

REM Gå ind i src-mappen
cd src

REM Sæt CMD-vinduets størrelse
mode con: cols=80 lines=25

echo Åbner program...
echo.

python main.py

echo.
echo Programmet er lukket.
pause
