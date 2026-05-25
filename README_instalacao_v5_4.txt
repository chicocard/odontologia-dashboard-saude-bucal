
ODONTOWORKFORCE BRASIL — DASHBOARD V5.4
=======================================

Correção principal:
- A integração município-população agora não depende de uma regra fixa de código.
- O painel busca vários candidatos possíveis para o código municipal bruto da RAIS:
  * código original de 6 dígitos;
  * primeiros 6 dígitos;
  * últimos 6 dígitos;
  * versões sem zeros à esquerda;
  * versões preenchidas com zeros.
- Escolhe o candidato que existe na tabela territorial `tabela_regioes(1).csv`.

Por que isso é diferente das V5.2/V5.3:
- As versões anteriores ainda aplicavam uma regra determinística.
- A V5.4 valida o código contra a própria tabela de municípios/regiões.

Como rodar:
1. Copie dashboard_final_v5_4.py e run_dashboard_v5_4.ps1 para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   .\run_dashboard_v5_4.ps1

3. Abra:
   http://localhost:8512

Depois confira em Exportações:
- Diagnóstico da integração município-população
- Diagnóstico dos códigos municipais originais

O percentual integrado deve ficar próximo de 100% em todos os anos.
