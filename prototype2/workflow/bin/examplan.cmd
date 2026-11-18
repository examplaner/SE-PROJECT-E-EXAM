@echo off
rem Find run.py relative to this launcher so it works from any folder.
"%USERPROFILE%\anaconda3\python.exe" -B "%~dp0..\run.py"
exit /b %errorlevel%
