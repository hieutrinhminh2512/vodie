@echo off
chcp 65001 > nul
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
echo ===================================================
echo     VODIE AI HORROR STUDIO - WEB DASHBOARD
echo ===================================================
echo Đang khởi động phòng thu tại http://localhost:8000 ...

start "" "http://localhost:8000"
python -m uvicorn src.studio.server:app --host 0.0.0.0 --port 8000 --reload
pause
