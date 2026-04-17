@echo off

echo.
echo  -- LFS Setup ----------------------------------

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python not found.
    echo  Install Python from https://python.org and re-run setup.bat
    echo.
    pause
    exit /b 1
)

echo  Installing Python dependencies...
echo.
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo  [ERROR] Dependency installation failed.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo  -- Configuring AWS credentials ---------------
echo.
python "%~dp0cli.py" setup
if errorlevel 1 (
    echo.
    echo  [ERROR] Setup did not complete. Check the error above.
    echo.
    pause
    exit /b 1
)

echo.
echo  Setup complete! You can now run:
echo    LFS upload ^<project^> ^<file^>
echo    LFS download ^<project^> ^<file^>
echo    LFS list ^<project^>
echo.
