@echo off
chcp 65001 > nul
echo ===================================================
echo     VODIE TEST SUITE - AUTOMATED UNIT TESTS
echo ===================================================
python -m pytest tests/ -v
pause
