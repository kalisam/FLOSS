@echo off
REM Windows launcher for Desktop Pony Swarm
REM Sets PYTHONPATH and runs the swarm

REM Get the directory where this script is located
SET SCRIPT_DIR=%~dp0

REM Set PYTHONPATH to include project root
SET PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

REM Run the swarm
python "%SCRIPT_DIR%\run_swarm.py" %*
