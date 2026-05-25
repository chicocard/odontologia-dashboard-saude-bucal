
ODONTOWORKFORCE BRASIL — DASHBOARD V5.2
=======================================

Correção principal:
- Corrige normalização de código municipal.
- O problema provável era usar sempre os 6 últimos dígitos do código municipal.
- Isso distorce códigos IBGE de 7 dígitos, por exemplo 3106200 -> 106200.
- A V5.2 usa:
  * 7 ou mais dígitos: primeiros 6 dígitos;
  * 6 dígitos: mantém os 6;
  * menos de 6: completa com zeros à esquerda.

Por que isso importa:
- Se os códigos municipais de 2020–2022 vieram em formato diferente de 2019,
  a integração com população e regiões ficava incompleta.
- Isso explicava taxas per capita artificialmente baixas após 2019.

Instalação:
1. Copie dashboard_final_v5_2.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v5_2.py

2. Copie run_dashboard_v5_2.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\run_dashboard_v5_2.ps1

3. Rode:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   .\run_dashboard_v5_2.ps1

4. Abra:
   http://localhost:8510

Na aba Exportações, confira:
- Diagnóstico da integração município-população
- percentual_integrado deve ficar próximo de 100% em todos os anos.
