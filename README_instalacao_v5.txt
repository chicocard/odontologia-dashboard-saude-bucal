
ODONTOWORKFORCE BRASIL — DASHBOARD V5
=====================================

Arquivos:
- dashboard_final_v5.py
- run_dashboard_v5.ps1

Instalação:
1. Copie dashboard_final_v5.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v5.py

2. Copie run_dashboard_v5.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\run_dashboard_v5.ps1

3. No PowerShell:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   .\run_dashboard_v5.ps1

4. Abra:
   http://localhost:8508

Melhorias principais:
- Layout reorganizado com hero, cartões, abas limpas e menos poluição visual.
- Filtros em grupos: período, território, especialidades, perfil/vínculo e apresentação.
- Especialidades/CBO com seleção por grupo, família, busca, top-N ou escolha manual.
- Códigos de sexo, raça/cor, tipo de vínculo, natureza jurídica e CNAE convertidos para nomes legíveis.
- Barras horizontais em setor/vínculo, evitando colunas únicas ilegíveis.
- Taxas per capita, boxplots, regiões de saúde e macrorregiões.
- Exportações em CSV/Excel.
