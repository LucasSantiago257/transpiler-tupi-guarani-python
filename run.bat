@echo off
REM ============================================================
REM  Transpilador Tupi - inicializador do visualizador grafico
REM  Basta dar dois cliques neste arquivo.
REM ============================================================
setlocal
cd /d "%~dp0"

echo Instalando/verificando dependencias (lark, click, streamlit)...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERRO: nao foi possivel instalar as dependencias.
    echo Verifique se o Python esta instalado e no PATH.
    echo.
    pause
    exit /b 1
)

echo.
echo Abrindo o visualizador no navegador... (feche esta janela para encerrar)
python -m streamlit run app.py

pause
endlocal
