@echo off
title sales-list-builder
chcp 65001 >nul

cd /d "%~dp0"

REM ========== Python チェック ==========
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python がインストールされていません。
    echo.
    echo 対処: https://www.python.org/downloads/ から Python 3.11 以上をインストールしてください。
    echo       インストール時に "Add Python to PATH" にチェックを入れてください。
    echo.
    pause
    exit /b 1
)

REM ========== .env チェック ==========
if not exist "%~dp0.env" (
    echo.
    echo [ERROR] .env ファイルが見つかりません。
    echo.
    echo 対処: .env.example をコピーして .env にリネームし、
    echo       GOOGLE_API_KEY=あなたのAPIキー を記入してください。
    echo.
    echo       配置先: %~dp0.env
    echo.
    pause
    exit /b 1
)

REM ========== 依存ライブラリチェック ==========
set MISSING_LIBS=

python -c "import pandas" >nul 2>&1
if errorlevel 1 set MISSING_LIBS=%MISSING_LIBS% pandas

python -c "import requests" >nul 2>&1
if errorlevel 1 set MISSING_LIBS=%MISSING_LIBS% requests

python -c "import dotenv" >nul 2>&1
if errorlevel 1 set MISSING_LIBS=%MISSING_LIBS% python-dotenv

python -c "import bs4" >nul 2>&1
if errorlevel 1 set MISSING_LIBS=%MISSING_LIBS% beautifulsoup4

if not "%MISSING_LIBS%"=="" (
    echo.
    echo [ERROR] 以下の依存ライブラリが不足しています:
    echo         %MISSING_LIBS%
    echo.
    echo 対処: 以下のコマンドを実行してください。
    echo       cd ^<workspace^>\packages\sales-list-builder
    echo       pip install -r requirements.txt
    echo       pip install -e .
    echo.
    pause
    exit /b 1
)

REM ========== sales_list_builder インポートチェック ==========
python -c "import sales_list_builder" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] sales_list_builder パッケージが認識されていません。
    echo.
    echo 対処: 以下のコマンドを実行してください。
    echo       cd ^<workspace^>\packages\sales-list-builder
    echo       pip install -r requirements.txt
    echo       pip install -e .
    echo.
    pause
    exit /b 1
)

echo.
echo sales-list-builder 起動中...
echo.

python src\tools\main.py

echo.
echo ==========================
echo 処理終了
echo ==========================
pause
