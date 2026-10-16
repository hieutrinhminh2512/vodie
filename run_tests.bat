@echo off
chcp 65001 > nul
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
echo ===================================================
echo     VODIE TEST SUITE - AUTOMATED UNIT TESTS
echo ===================================================
python -m pytest tests/ -v
pause
