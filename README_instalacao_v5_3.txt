
ODONTOWORKFORCE BRASIL — DASHBOARD V5.3
=======================================

Correção principal:
- Corrige novamente a normalização do código municipal.
- A V5.2 assumia que códigos com 7 dígitos eram sempre IBGE completo, usando os 6 primeiros.
- Porém alguns anos podem vir como 0 + código municipal de 6 dígitos:
  exemplo 0310620 -> correto: 310620.
- A V5.3 diferencia:
  * 7 dígitos começando com 0: usa os 6 últimos;
  * 7 dígitos sem zero inicial: usa os 6 primeiros;
  * 6 dígitos: mantém.

Diagnóstico adicional:
- Aba Exportações agora mostra "Diagnóstico dos códigos municipais originais",
  com tamanho do código municipal por ano, exemplos mínimo/máximo e códigos distintos.

Instalação:
1. Copie dashboard_final_v5_3.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\dashboard_final_v5_3.py

2. Copie run_dashboard_v5_3.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\run_dashboard_v5_3.ps1

3. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   .\run_dashboard_v5_3.ps1

4. Abra:
   http://localhost:8511
