
DIAGNÓSTICO DA DISCREPÂNCIA DAS TAXAS
=====================================

Este pacote NÃO cria outra versão do dashboard.

Ele testa diretamente, no seu computador, o banco:
C:\rais-intelligence-data\database\odontologia_workforce.duckdb

E a tabela territorial:
C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\reference\tabela_regioes(1).csv

Como rodar:

1. Copie diagnostico_discrepancia_taxas.py para:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. No PowerShell:

   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\diagnostico_discrepancia_taxas.py

3. O script vai gerar:
   diagnostico_discrepancia_taxas.xlsx

4. Envie ou cole aqui principalmente as tabelas:
   - match_estrategias
   - algum_candidato_valido
   - resumo_taxas
   - perfil_codigos
   - nao_integrados_top

Objetivo:
- verificar se 2020-2022 estão perdendo vínculos na integração município-população;
- testar várias estratégias de normalização do código municipal;
- calcular as taxas fora do dashboard, diretamente do banco.
