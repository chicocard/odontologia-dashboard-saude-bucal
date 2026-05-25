
ODONTOWORKFORCE BRASIL — DASHBOARD V6.5 SAÚDE BUCAL
===================================================

Correção principal:
- Remove completamente a dependência de matplotlib.
- Corrige o erro:
  ModuleNotFoundError: No module named 'matplotlib'
- Mantém os mapas, mas agora desenhados com Plotly diretamente por polígonos,
  sem px.choropleth e sem matplotlib.

Como instalar:
1. Feche o Streamlit atual.
2. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3
   Substitua arquivos quando o Windows perguntar.

3. Rode:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\diagnosticar_geojson.py
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v6_5_saude_bucal.py --server.port 8524 --server.address localhost

4. Abra:
   http://localhost:8524
