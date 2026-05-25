
ODONTOWORKFORCE BRASIL — DASHBOARD V5.7 SAÚDE BUCAL
===================================================

Objetivo:
- Versão consolidada do dashboard de Saúde Bucal.
- Remove referências repetidas ao Boletim no corpo do painel.
- Mantém apenas uma seção "Fonte do modelo analítico".
- Usa recorte estrito de Saúde Bucal:
  * CD: CBO 2232*
  * TSB: 322405
  * ASB: 322415 e 322430
  * TPD: 322410 e 322425
  * APD: 322420

Arquivos:
- dashboard_final_v5_7_saude_bucal.py
- run_dashboard_v5_7_saude_bucal.ps1
- reference/cbo_odontologia_mapa.csv
- scripts/atualizar_mapa_cbo_odontologia.py

Instalação:
1. Extraia este ZIP dentro de:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute no PowerShell:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py

3. Rode o dashboard diretamente com Python, sem depender de política de execução do PowerShell:
   python -m streamlit run .\dashboard_final_v5_7_saude_bucal.py --server.port 8516 --server.address localhost

4. Abra:
   http://localhost:8516
