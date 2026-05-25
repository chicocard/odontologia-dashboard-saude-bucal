
ODONTOWORKFORCE BRASIL — DASHBOARD V5.8 SAÚDE BUCAL
===================================================

Melhoria principal:
- Aba Território redesenhada para tornar os boxplots mais interpretáveis.
- O gráfico confuso de boxplots foi substituído por uma sequência analítica:
  1. seleção de nível territorial;
  2. seleção de categoria ocupacional;
  3. boxplot com controle de escala;
  4. ranking horizontal dos territórios;
  5. dispersão população × densidade;
  6. tabela territorial exportável.

Controles novos:
- Nível territorial:
  * UF
  * Macrorregião de saúde
  * Região de saúde
  * Município
- Categoria:
  * Total Saúde Bucal
  * CD
  * TSB
  * ASB
  * TPD
  * APD
  * Outras
- Escala:
  * Normal
  * Zoom até P95
  * Zoom até P99
  * Logarítmica
- Mostrar/ocultar pontos individuais no boxplot.

Como rodar:
1. Extraia dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v5_8_saude_bucal.py --server.port 8517 --server.address localhost

3. Abra:
   http://localhost:8517
