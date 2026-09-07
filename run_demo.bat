@echo off
python dist\DIKWP_MINEX_FABRIC_OS.pyz suite --root . --output outputs\demo
if errorlevel 1 exit /b %errorlevel%
echo Open web\DIKWP_MINEX_FABRIC_OS_Dashboard.html in a browser.
