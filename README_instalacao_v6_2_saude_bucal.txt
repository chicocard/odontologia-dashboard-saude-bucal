
ODONTOWORKFORCE BRASIL — DASHBOARD V6.2 SAÚDE BUCAL
===================================================

Correção dos mapas:
- Busca os GeoJSONs de forma recursiva, inclusive se o ZIP tiver sido extraído em subpasta.
- Troca a chave interna do mapa para "match_id", mais estável no Plotly.
- Exibe diagnóstico no próprio dashboard:
  * número de feições cartográficas;
  * número de territórios do painel;
  * número de territórios encontrados no mapa.
- Inclui script local:
  scripts/diagnosticar_geojson.py

Como rodar:
1. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Rode:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\diagnosticar_geojson.py
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v6_2_saude_bucal.py --server.port 8521 --server.address localhost

3. Abra:
   http://localhost:8521
