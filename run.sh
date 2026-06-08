#!/usr/bin/env bash
# ============================================================
#  Transpilador Tupi - inicializador do visualizador gráfico
#  Uso: ./run.sh   (no macOS/Linux)
# ============================================================
set -e
cd "$(dirname "$0")"

echo "Instalando/verificando dependências (lark, click, streamlit)..."
python3 -m pip install -q -r requirements.txt

echo
echo "Abrindo o visualizador no navegador... (Ctrl+C para encerrar)"
python3 -m streamlit run app.py
