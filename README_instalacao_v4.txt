OdontoWorkforce Brasil - Dashboard V4
====================================

Arquivos:
- dashboard_final_v4.py
- run_dashboard_v4.ps1
- reference/tabela_regioes(1).csv
- reference/populacao_tcu_municipios.csv
- reference/populacao_tcu_uf.csv
- reference/cbo_odontologia_mapa.csv

Instalação sugerida:
1. Copie dashboard_final_v4.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v4.py

2. Copie run_dashboard_v4.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\run_dashboard_v4.ps1

3. Copie a pasta reference/ para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\reference\

4. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   .\run_dashboard_v4.ps1

5. Abra:
   http://localhost:8507

Melhorias principais:
- seleção de CBO por grupo ocupacional, família de especialidade, busca textual e top N;
- rótulos legíveis para CBOs odontológicos;
- nomes legíveis nas colunas exibidas/exportadas;
- filtros adicionais por sexo, raça/cor, setor/tipo de vínculo;
- boxplots e taxas per capita por município, região e macrorregião.
