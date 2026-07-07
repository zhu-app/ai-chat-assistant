@echo off
setlocal
cd /d "%~dp0"
if exist "tmp_rag_run.log" del /f /q "tmp_rag_run.log"
if exist "tmp_rag_report.json" del /f /q "tmp_rag_report.json"
"%~dp0.venv\Scripts\python.exe" "%~dp0tmp_rag_service_validation.py" > "%~dp0tmp_rag_run.log" 2>&1
echo exit_code=%ERRORLEVEL%>>"%~dp0tmp_rag_run.log"
endlocal