@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   MOTION SETUP - TOOL KURULUM
echo ============================================
echo.

set DEFAULT_CORE=..\aktapokus-core
set /p CORE_PATH=Core klasoru nerede? [%DEFAULT_CORE%]:
if "%CORE_PATH%"=="" set CORE_PATH=%DEFAULT_CORE%

if not exist "%CORE_PATH%\core\docker-compose.yml" goto BADCORE
if not exist "%CORE_PATH%\.env" goto NOENV

echo [1/2] Dosyalar kopyalaniyor: %CORE_PATH%\tools\motionsetup\
if not exist "%CORE_PATH%\tools\motionsetup" mkdir "%CORE_PATH%\tools\motionsetup"
robocopy . "%CORE_PATH%\tools\motionsetup" /E /XF setup.bat uninstall.bat /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto COPYFAIL

echo [2/2] Container yeniden baslatiliyor...
pushd "%CORE_PATH%\core"
docker compose restart app
if errorlevel 1 goto BUILDFAIL
popd

echo.
echo ============================================
echo   MOTION SETUP KURULDU
echo ============================================
echo   Arayuzu yenileyin: http://localhost:8000
echo   Tool listesinde "Motion Setup" gorunmeli.
echo ============================================
pause
exit /b 0

:BADCORE
echo [HATA] Belirtilen yolda aktapokus-core bulunamadi: %CORE_PATH%
echo        core\docker-compose.yml orada olmali.
pause
exit /b 1

:NOENV
echo [HATA] %CORE_PATH%\.env bulunamadi.
echo        Once core klasorunde setup.bat'i calistirip core kurulumunu
echo        tamamlayin, sonra bu betigi tekrar calistirin.
pause
exit /b 1

:COPYFAIL
echo [HATA] Dosyalar kopyalanamadi.
pause
exit /b 1

:BUILDFAIL
echo [HATA] Container yeniden baslatilamadi. Yukaridaki hatayi kontrol edin.
popd
pause
exit /b 1
