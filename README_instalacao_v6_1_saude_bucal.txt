
ODONTOWORKFORCE BRASIL — DASHBOARD V6.1 SAÚDE BUCAL
===================================================

Correção principal:
- Remove a criação/atualização de VIEW dentro do Streamlit.
- Corrige o erro DuckDB:
  "Can't open a connection to same database file with a different configuration than existing connections"

Causa:
- A V6.0 abria uma conexão de escrita para CREATE OR REPLACE VIEW.
- Em seguida, o Streamlit mantinha/cacheava conexões read_only=True.
- Em reruns, por exemplo ao mudar o formato do boxplot, o DuckDB bloqueava abrir o mesmo arquivo com configuração diferente.

Solução:
- A V6.1 usa diretamente a tabela odontologia_vinculos.
- O recorte estrito de Saúde Bucal é aplicado como filtro SQL em todas as consultas:
  CD = CBO 2232*
  TSB = 322405
  ASB = 322415 e 322430
  TPD = 322410 e 322425
  APD = 322420

Como instalar:
1. Extraia este ZIP em:
   C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3

2. Execute:
   Set-Location "C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3"
   & "C:\Projetos\odontologia_workforce_app\.venv\Scripts\Activate.ps1"
   python .\scripts\atualizar_mapa_cbo_odontologia.py
   python -m streamlit run .\dashboard_final_v6_1_saude_bucal.py --server.port 8520 --server.address localhost

3. Abra:
   http://localhost:8520
