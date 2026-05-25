
ODONTOWORKFORCE BRASIL — DASHBOARD V5.9 SAÚDE BUCAL
===================================================

Melhorias principais:
- Boxplots da aba Território redesenhados com opção de:
  * violino suave + caixa interna;
  * box plot clássico;
  * zoom P95/P99;
  * escala logarítmica;
  * exibição opcional dos pontos.
- Inclusão de mapas coropléticos:
  * distribuição espacial por UF;
  * distribuição espacial por município;
  * taxa per capita por 10 mil habitantes;
  * vínculos absolutos.
- Inclusão de ranking e tabela do mapa.

Arquivos cartográficos esperados:
- assets/br_ufs.geojson
- assets/br_municipios.geojson

Como rodar:
1. Extraia dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v5_9_saude_bucal.py --server.port 8518 --server.address localhost

3. Abra:
   http://localhost:8518
