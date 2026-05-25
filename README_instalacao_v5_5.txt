
ODONTOWORKFORCE BRASIL — DASHBOARD V5.5
=======================================

Melhoria principal:
- Seleção de CBO refeita para não usar rótulos compostos como chave.
- O filtro usa internamente apenas o código CBO.
- Os nomes completos aparecem por format_func, apenas para visualização.
- Isso evita problemas com seleções baseadas em vários campos.

Também inclui:
- reference/cbo_odontologia_mapa.csv
- scripts/atualizar_mapa_cbo_odontologia.py

Instalação:
1. Copie dashboard_final_v5_5.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v5_5.py

2. Copie run_dashboard_v5_5.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\run_dashboard_v5_5.ps1

3. Copie a pasta reference para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\reference

4. Copie a pasta scripts para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\scripts

5. Antes de abrir o dashboard, rode uma vez:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py

6. Depois rode:
   .\run_dashboard_v5_5.ps1

7. Abra:
   http://localhost:8513
