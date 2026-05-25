
ODONTOWORKFORCE BRASIL — DASHBOARD V6.4 SAÚDE BUCAL
===================================================

Correção principal:
- A parte dos mapas foi refeita.
- O mapa não usa mais px.choropleth/Plotly para os polígonos do TabWin.
- Agora o mapa é desenhado como coroplético estático com matplotlib, mais estável para os GeoJSONs derivados de .MAP.
- Corrige:
  * estados desaparecendo ou aparecendo parcialmente;
  * mapa com poucos estados;
  * título sobreposto à legenda;
  * legenda mal posicionada.

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
   python -m streamlit run .\dashboard_final_v6_4_saude_bucal.py --server.port 8523 --server.address localhost

4. Abra:
   http://localhost:8523

Observação:
- O mapa municipal nacional pode ser mais pesado. Para leitura nacional, comece em UF.
- Para município, filtre uma UF ou região antes.
