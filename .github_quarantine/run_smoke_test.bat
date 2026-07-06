@echo off
echo.
echo ============================================================
echo   THE QUANT COUNCIL - SMOKE TEST (17 checks)
echo ============================================================
echo.
.venv\Scripts\python.exe smoke_test.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [ALL TESTS PASSED] Pipeline is ready.
) else (
    echo.
    echo [FAILURES DETECTED] Review the output above.
)
pause
