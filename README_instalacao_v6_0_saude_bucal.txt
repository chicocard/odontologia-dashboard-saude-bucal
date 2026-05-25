
ODONTOWORKFORCE BRASIL — DASHBOARD V6.0 SAÚDE BUCAL
===================================================

Correção principal:
- Inclui os arquivos cartográficos GeoJSON necessários para os mapas:
  * assets/br_ufs.geojson
  * assets/br_municipios.geojson

Esses GeoJSONs foram convertidos a partir do mapas.zip enviado, usando:
- br_uf.MAP
- br_municip.MAP

Arquivos principais:
- dashboard_final_v6_0_saude_bucal.py
- assets/br_ufs.geojson
- assets/br_municipios.geojson
- scripts/converter_mapas_tabwin_para_geojson.py

Como instalar:
1. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

A estrutura deve ficar:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v6_0_saude_bucal.py
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\assets\br_ufs.geojson
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\assets\br_municipios.geojson

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v6_0_saude_bucal.py --server.port 8519 --server.address localhost

3. Abra:
   http://localhost:8519

Observação:
- O mapa municipal tem 5.570 polígonos e pode demorar um pouco mais para carregar.
- Se preferir regenerar os GeoJSONs no seu computador, copie mapas.zip para a pasta do projeto e rode:
   python .\scripts\converter_mapas_tabwin_para_geojson.py
