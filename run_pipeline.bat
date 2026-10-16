@echo off
chcp 65001 > nul
echo ===================================================
echo     VODIE AI HORROR STUDIO - PIPELINE RUNNER
echo ===================================================
python -u -m src.main --title "Chuyen_Ma_Da_Lat" --mood "kinh_di_nang"
echo.
echo Hoàn thành! Kiểm tra tệp xuất ra trong thư mục output/
pause
