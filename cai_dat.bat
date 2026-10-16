@echo off
chcp 65001 > nul
echo ===================================================
echo     VODIE - CAI DAT (chi can chay 1 lan)
echo ===================================================
where python >nul 2>nul || (echo Chua co Python. Tai Python 3.11+ tai https://www.python.org/downloads/ va tick "Add to PATH". & pause & exit /b 1)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (echo Cai dat loi. & pause & exit /b 1)
if not exist .env copy .env.example .env > nul
echo.
echo Dang tai model giong doc VieNeu-TTS va doc thu 1 cau...
python -c "from src.tts import TTSEngine; p=TTSEngine().synthesize(\"Xin chào, đây là giọng kể chuyện ma.\"); print(\"Da doc thu:\", p)"
echo.
echo Xong! Bam dup run_studio.bat de mo phong thu.
pause
