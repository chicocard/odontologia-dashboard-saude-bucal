
ODONTOWORKFORCE BRASIL — DASHBOARD V5.6
=======================================

Mudança principal:
- Primeira aba reformulada segundo o modelo analítico do Boletim Técnico 07 de Sociodemografia Odontológica.
- Removidos da aba executiva:
  * gráfico de número de municípios com vínculos;
  * gráfico de taxa agregada anual.
- Incluídas análises:
  * composição CD, TSB, ASB, TPD, APD e Outras;
  * participação percentual por categoria;
  * evolução da composição ocupacional;
  * densidade por UF e categoria, em vínculos por 10 mil habitantes;
  * razões CD/TSB e CD/ASB por UF;
  * tabela-súmula por UF com vínculos, taxas e razões.

Instalação:
1. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   .\run_dashboard_v5_6.ps1

3. Abra:
   http://localhost:8514
