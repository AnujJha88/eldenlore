@echo off
:: Navigate to the folder (Using Windows Path)
cd /d "D:/fun stuff/eldenlore"

echo ========================================
echo   ELDEN RING LORE SCRAPER
echo ========================================
echo.

:: ------------------------------------------------------
:: STEP 1: Run Reddit Scraper
:: ------------------------------------------------------
echo [1/3] Running Reddit scraper...
python scraper.py
if errorlevel 1 (
    echo ERROR: Reddit scraper failed!
    pause
    exit /b 1
)
echo.

:: ------------------------------------------------------
:: STEP 2: Run Alternative Sources Scraper
:: ------------------------------------------------------


:: ------------------------------------------------------
:: STEP 3: Push Data using WSL Git
:: ------------------------------------------------------
echo [3/3] Pushing to GitHub...
wsl git add lore_data.json lore_data_alternative.json
wsl git commit -m "Daily lore update - %date% %time%"
wsl git push origin main

echo.
echo ========================================
echo   COMPLETE! Data updated on GitHub Pages
echo ========================================
pause