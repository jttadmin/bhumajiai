@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run install_windows.bat first.
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name UniversalInterviewAssistant --collect-all sounddevice --collect-all soundfile --hidden-import keyring.backends.Windows --hidden-import keyboard run.py
if errorlevel 1 exit /b 1
echo Built: dist\UniversalInterviewAssistant.exe
