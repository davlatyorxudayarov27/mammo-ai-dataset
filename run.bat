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
  echo [setup] GPU uchun CUDA torch (cu128) o'rnatilmoqda (RTX 5070 / Blackwell)...
  echo [setup] requirements.txt CPU torch tortadi — uni CUDA build bilan almashtiramiz.
  pip install --force-reinstall torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
  if errorlevel 1 (
    echo [ogohlantirish] CUDA torch o'rnatilmadi — GPU o'rniga CPU rejimida ishlashi mumkin.
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
echo [run] http://127.0.0.1:8002  (LOCAL_DICOM_ROOT=%LOCAL_DICOM_ROOT%)
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
