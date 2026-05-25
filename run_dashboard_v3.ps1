$env:PYTHONPATH = "$PWD\src"
python -m streamlit run .\dashboard_final_v3.py --server.port 8506 --server.address localhost
