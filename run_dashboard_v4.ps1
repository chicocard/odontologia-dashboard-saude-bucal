$env:PYTHONPATH = "$PWD\src"
python -m streamlit run .\dashboard_final_v4.py --server.port 8507 --server.address localhost
