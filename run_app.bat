@echo off
cd /d "C:\Users\sjeon046\Desktop\meal-planner"
call .venv\Scripts\activate.bat
streamlit run app.py
pause