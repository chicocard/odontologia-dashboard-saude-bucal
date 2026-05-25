
ODONTOWORKFORCE BRASIL — DASHBOARD V6.3 SAÚDE BUCAL
===================================================

Correção principal dos mapas:
- A conversão anterior dos arquivos .MAP do TabWin estava incluindo indevidamente o ponto de rótulo/centróide como se fosse vértice do polígono.
- Isso distorcia os polígonos e fazia o mapa aparecer como um grande bloco/retângulo azul.
- A V6.3 substitui os GeoJSONs por arquivos corrigidos e validados.

Arquivos corrigidos:
- assets/br_ufs.geojson
- assets/br_municipios.geojson

Como instalar:
1. Feche o Streamlit atual.
2. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3
   Use "substituir arquivos" quando o Windows perguntar.

3. Rode:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\diagnosticar_geojson.py
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v6_3_saude_bucal.py --server.port 8522 --server.address localhost

4. Abra:
   http://localhost:8522

Observação:
- Se o navegador mantiver cache visual, use Ctrl+F5.
