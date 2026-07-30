@echo off
chcp 65001 >nul

:: Doi thu muc ve thu muc chua file BAT (tranh loi duong dan tuong doi)
cd /d "%~dp0"

echo =======================================================
echo     HE THONG TAO BAN TIN SANG TU DONG (VIRA)
echo =======================================================
echo.

:: Lay ngay hien tai (YYYY-MM-DD) - dung PowerShell thay wmic (wmic da bi deprecated tren Win11)
for /f "usebackq" %%I in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'"`) do set TODAY=%%I

echo Ngay xu ly: %TODAY%
echo.

:: -------------------------------------------------------
echo [1/5] Dang thu thap tin Vi mo (VIRA)...
python -X utf8 "workflow\scripts\collect_vira_pdf.py" --date %TODAY%
if errorlevel 1 (
    echo [CANH BAO] Buoc 1 gap loi, tiep tuc...
)
echo.

:: -------------------------------------------------------
echo [2/5] Dang thu thap tin Doanh nghiep (HOSE)...
python -X utf8 "workflow\scripts\collect_hsx_news.py" --date %TODAY%
if errorlevel 1 (
    echo [CANH BAO] Buoc 2 gap loi, tiep tuc...
)
echo.

:: -------------------------------------------------------
echo [3/5] Dang thu thap Goc nhin Chuyen gia (Vietstock)...
python -X utf8 "workflow\scripts\collect_vietstock_rss.py" --date %TODAY%
if errorlevel 1 (
    echo [CANH BAO] Buoc 3 gap loi, tiep tuc...
)
echo.

:: -------------------------------------------------------
echo [4/5] Dang ve Bieu do Thi truong...
python -X utf8 "workflow\scripts\draw_charts.py"
if errorlevel 1 (
    echo [CANH BAO] Buoc 4 gap loi, tiep tuc...
)
echo.

:: -------------------------------------------------------
echo [5/5] Dang tong hop va xuat file PDF...
python -X utf8 "workflow\scripts\export_vira_pdf.py" --date %TODAY% --open
if errorlevel 1 (
    echo [LOI] Buoc 5 that bai! Kiem tra log de biet chi tiet.
    echo.
    echo =======================================================
    echo HOAN TAT VOI LOI - Kiem tra thong bao phia tren.
    echo =======================================================
    pause
    exit /b 1
)

echo.
echo =======================================================
echo HOAN TAT! Ban tin da duoc mo len.
echo =======================================================
pause
