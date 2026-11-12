@echo off
setlocal
cd /d "%~dp0\.."
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Python 3 puuttuu.
  echo Asenna Python 3 osoitteesta https://www.python.org/
  echo Katso sitten editor\VAATIMUKSET.txt
  pause
  exit /b 1
)
%PY% -m editor
if errorlevel 1 (
  echo.
  echo Kaynnistys ei onnistunut. Katso editor\VAATIMUKSET.txt
  echo Tata tiedostoa ei asenna ohjelmia.
  pause
  exit /b 1
)
