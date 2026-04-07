@echo off
cd /d %~dp0
chcp 65001 > nul
call venv\Scripts\activate


rem     pyinstaller --onefile  ".\MHO_Achi_Locale_tool.py"
rem python -m PyInstaller --onefile --noconsole --name CalcClipboardCleaner clear_rn.py

rem  PyInstaller EasyReady.py --onefile --windowed ^

python -m PyInstaller EasyReady.py ^
--icon=./images/EasyReady.ico  --onefile --windowed ^
--add-data "images;images"


pause