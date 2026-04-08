@echo off
cd /d %~dp0
if not exist .venv (
  echo [ERROR] .venv not found. Please run the setup in SETUP_LOCAL.md first.
  exit /b 1
)
call .venv\Scripts\activate.bat
python server_main.py --port 6400 --reload
