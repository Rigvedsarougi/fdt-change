pip install --upgrade virtualenv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
deactivate
