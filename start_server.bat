@echo off
echo Starting FastAPI server...
cd /d "%~dp0"
python -m uvicorn app:app --reload
