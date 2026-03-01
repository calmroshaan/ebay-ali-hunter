@echo off
title eBay Ali Hunter
color 0A

echo.
echo  ================================
echo   eBay Ali Hunter - Starting...
echo  ================================
echo.

:: Change to the folder where this .bat file lives
cd /d "%~dp0"

:: Run the UI
python ui/app.py

:: Clean exit message
echo.
echo  ================================
echo   Tool stopped. Window closing...
echo  ================================
timeout /t 3 > nul