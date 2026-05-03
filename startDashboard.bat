@echo off
echo ================================
echo   IHSG Fear ^& Greed Dashboard
echo ================================
echo.
call venv\Scripts\activate
echo [OK] Virtual environment aktif
echo.
echo Membuka dashboard...
echo Tekan CTRL+C untuk stop
echo.
streamlit run app.py
pause