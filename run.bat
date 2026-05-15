@echo off
setlocal
cd /d "%~dp0"

if not exist .venv (
  echo [setup] yangi virtualenv yaratilmoqda...
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo [xato] virtualenv yaratilmadi. Python 3.12 o'rnatilganligini tekshiring.
    exit /b 1
  )
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 (
    echo [xato] paketlar o'rnatilmadi.
    exit /b 1
  )
) else (
  call .venv\Scripts\activate.bat
)

if "%LOCAL_DICOM_ROOT%"=="" (
  if exist "d:\Project_MAMOGRAF\dicomfiles" (
    set "LOCAL_DICOM_ROOT=d:\Project_MAMOGRAF\dicomfiles"
  )
)

echo.
echo [run] http://127.0.0.1:8000  (LOCAL_DICOM_ROOT=%LOCAL_DICOM_ROOT%)
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
