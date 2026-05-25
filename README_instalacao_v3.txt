
ODONTOWORKFORCE BRASIL — DASHBOARD V3
=====================================

Esta versão incorpora as populações estimadas IBGE/TCU enviadas pelo usuário e melhora as análises per capita.

Arquivos principais
-------------------
1. dashboard_final_v3.py
   Painel avançado com filtros territoriais, CBO, boxplots e taxas per capita.

2. run_dashboard_v3.ps1
   Script para rodar o painel na porta 8506.

3. reference/tabela_regioes(1).csv
   Tabela de municípios, regiões de saúde, macrorregiões e população IBGE 2022.

4. reference/populacao_tcu_municipios.csv
   Arquivo normalizado a partir das planilhas IBGE/TCU:
   - estimativa_dou_2020.xlsx
   - estimativa_dou_2021.xlsx
   - estimativa_dou_2024.xlsx
   - estimativa_dou_2025.xlsx
   Inclui também 2022 derivado da tabela_regioes(1).csv.

5. reference/populacao_tcu_uf.csv
   Série UF 2001-2019 extraída de serie_2001_2019_TCU.xlsx.
   Observação: o arquivo 2001-2019 enviado contém UF/região, não municípios. Por isso,
   para taxas municipais de 2019 o painel usa fallback para o ano municipal mais próximo disponível.

Instalação
----------
Copie os arquivos para:

C:\Projetos\odontologia_workforce_app\dashboard_final_v3.py
C:\Projetos\odontologia_workforce_app\run_dashboard_v3.ps1
C:\Projetos\odontologia_workforce_app\reference\tabela_regioes(1).csv
C:\Projetos\odontologia_workforce_app\reference\populacao_tcu_municipios.csv
C:\Projetos\odontologia_workforce_app\reference\populacao_tcu_uf.csv

Depois rode:

Set-Location "C:\Projetos\odontologia_workforce_app"
.\.venv\Scripts\Activate.ps1
.\run_dashboard_v3.ps1

Abra:

http://localhost:8506

Notas metodológicas
-------------------
- A RAIS usa código municipal de 6 dígitos sem dígito verificador.
- As planilhas DOU trazem COD. UF + COD. MUNIC, formando código IBGE de 7 dígitos.
- O normalizador usa os 6 primeiros dígitos para compatibilizar com RAIS e tabela_regioes.
- As taxas usam população municipal do mesmo ano quando disponível.
- Quando não há ano municipal exato, a população do ano disponível mais próximo é usada e marcada como fallback_ano_mais_proximo.
- Quando não há população municipal em nenhum arquivo, usa-se a população IBGE 2022 da tabela_regioes e marca fallback_2022.
