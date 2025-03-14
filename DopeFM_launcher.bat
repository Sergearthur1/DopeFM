@echo off
cd /d "%~dp0"  REM Se place dans le dossier du script
echo 🔥 Activation du venv...
call venvFM\Scripts\activate.bat
echo ✅ Venv activé !

echo 🚀 Lancement de Streamlit...
streamlit run interface.py start "" http://localhost:8501

echo 🛑 Fermeture...
pause