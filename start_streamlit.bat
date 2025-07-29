@echo off
cd C:\code\incident_report_app_Gemini
call venv\Scripts\activate
streamlit run app.py --server.headless true >> streamlit.log 2>&1