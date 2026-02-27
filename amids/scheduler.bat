@echo off
setlocal

REM Activate virtual environment (assumes .venv at project root)
call "%~dp0..\ .venv\Scripts\activate.bat"

REM Run AMIDS orchestrator
python "%~dp0main_orchestrator.py"

endlocal

