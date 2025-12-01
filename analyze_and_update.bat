@echo off
REM Analyze saved page sources and update screen detection code
REM Run this after the automation has saved some page source files

echo ========================================
echo   AI Analysis - Extract Screen Indicators
echo ========================================
echo.
echo This will:
echo   1. Analyze saved page source files
echo   2. Extract real screen indicators using AI
echo   3. Update the code with actual identifiers
echo.
echo Make sure you've run the automation script first
echo to generate page source files in page_sources/
echo.

python analyze_page_sources.py

pause

