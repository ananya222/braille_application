@echo off
setlocal
cd /d "%~dp0"
rem Optional: set PYTHON_EXE to a Python 3.12 x64 executable with build dependencies.
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8, 'Use Python 3.12 x64'"
if errorlevel 1 exit /b 1
rem --clean clears PyInstaller caches; --noconfirm replaces only its named output.
rem No broad recursive deletion or cross-shell filesystem cleanup.
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm BrailleValidator.spec
if errorlevel 1 exit /b 1
if "%BRAILLE_BUILD_CONSOLE%"=="1" (
  echo Build ready: %CD%\dist\BrailleValidatorDebug\BrailleValidatorDebug.exe
) else (
  echo Build ready: %CD%\dist\BrailleValidator\BrailleValidator.exe
)
