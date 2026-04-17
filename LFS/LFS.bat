@echo off
:: org-data.bat - Run the org-data CLI tool
:: Place this file in your system PATH to use from anywhere

SET SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%cli.py" %*
