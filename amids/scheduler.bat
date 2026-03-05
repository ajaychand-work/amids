@echo off
setlocal

REM Activate virtual environment (assumes .venv at project root)
call "%~dp0..\.venv\Scripts\activate.bat"

REM Run AMIDS orchestrator as a module to keep package imports valid
python -m amids.main_orchestrator

endlocal
