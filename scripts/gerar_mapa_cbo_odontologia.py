from pathlib import Path
import duckdb
import pandas as pd
import re

DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
OUT = Path(r"C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3\reference\cbo_odontologia_mapa.csv")

MAPA_BASE = {
    # Cirurgiões-dentistas — família 2232
    "223204": ("Cirurgião-dentista", "Cirurgiões-dentistas", "Clínica odontológica / geral"),
    "223208": ("Cirurgião-dentista — clínico geral", "Cirurgiões-dentistas", "Clínica odontológica / geral"),
    "223212": ("Cirurgião-dentista — auditor", "Cirurgiões-dentistas", "Auditoria, gestão e regulação"),
    "223216": ("Cirurgião-dentista — dentística", "Cirurgiões-dentistas", "Dentística / restauradora"),
    "223220": ("Cirurgião-dentista — disfunção temporomandibular e dor orofacial", "Cirurgiões-dentistas", "Dor orofacial / DTM"),
    "223224": ("Cirurgião-dentista — endodontista", "Cirurgiões-dentistas", "Endodontia"),
    "223228": ("Cirurgião-dentista — estomatologista", "Cirurgiões-dentistas", "Estomatologia"),
    "223232": ("Cirurgião-dentista — implantodontista", "Cirurgiões-dentistas", "Implantodontia"),
    "223236": ("Cirurgião-dentista — odontogeriatra", "Cirurgiões-dentistas", "Odontogeriatria"),
    "223240": ("Cirurgião-dentista — odontologia do trabalho", "Cirurgiões-dentistas", "Odontologia do trabalho"),
    "223244": ("Cirurgião-dentista — odontologia para pacientes com necessidades especiais", "Cirurgiões-dentistas", "Pacientes com necessidades especiais"),
    "223248": ("Cirurgião-dentista — odontopediatra", "Cirurgiões-dentistas", "Odontopediatria"),
    "223252": ("Cirurgião-dentista — ortopedista e ortodontista", "Cirurgiões-dentistas", "Ortodontia / ortopedia funcional"),
    "223256": ("Cirurgião-dentista — patologista bucal", "Cirurgiões-dentistas", "Patologia bucal"),
    "223260": ("Cirurgião-dentista — periodontista", "Cirurgiões-dentistas", "Periodontia"),
    "223264": ("Cirurgião-dentista — protesiólogo bucomaxilofacial", "Cirurgiões-dentistas", "Prótese bucomaxilofacial"),
    "223268": ("Cirurgião-dentista — protesista", "Cirurgiões-dentistas", "Prótese dentária"),
    "223272": ("Cirurgião-dentista — radiologista", "Cirurgiões-dentistas", "Radiologia odontológica / imaginologia"),
    "223276": ("Cirurgião-dentista — saúde coletiva", "Cirurgiões-dentistas", "Saúde coletiva / saúde pública"),
    "223280": ("Cirurgião-dentista — traumatologista bucomaxilofacial", "Cirurgiões-dentistas", "Cirurgia e traumatologia bucomaxilofacial"),
    "223284": ("Cirurgião-dentista — odontologia legal", "Cirurgiões-dentistas", "Odontologia legal"),
    "223288": ("Cirurgião-dentista — odontologia estética", "Cirurgiões-dentistas", "Odontologia estética"),
    "223293": ("Cirurgião-dentista — acupunturista", "Cirurgiões-dentistas", "Práticas integrativas / acupuntura"),
    "223296": ("Cirurgião-dentista — homeopata", "Cirurgiões-dentistas", "Práticas integrativas / homeopatia"),

    # Técnicos e auxiliares de saúde bucal / prótese dentária
    "322405": ("Técnico em saúde bucal", "Equipe auxiliar odontológica", "Técnico em saúde bucal"),
    "322410": ("Protético dentário", "Equipe auxiliar odontológica", "Prótese dentária"),
    "322415": ("Auxiliar em saúde bucal", "Equipe auxiliar odontológica", "Auxiliar em saúde bucal"),
    "322420": ("Auxiliar de prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"),
    "322425": ("Técnico em prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"),

    # Possíveis códigos auxiliares/relacionados que podem aparecer dependendo do filtro do ETL
    "515105": ("Agente comunitário de saúde", "Apoio à atenção primária", "Atenção primária / apoio territorial"),
    "515110": ("Atendente de enfermagem", "Apoio assistencial", "Apoio assistencial"),
    "422105": ("Recepcionista", "Apoio administrativo em serviços de saúde", "Recepção / administrativo"),
    "411010": ("Assistente administrativo", "Apoio administrativo em serviços de saúde", "Administrativo"),
    "514120": ("Zelador / trabalhador de serviços de conservação", "Apoio operacional", "Apoio operacional"),
}

def only_digits(x):
    if x is None:
        return ""
    return re.sub(r"[^0-9]", "", str(x))

con = duckdb.connect(str(DB_PATH), read_only=True)

cols = con.execute("DESCRIBE odontologia_vinculos").fetchdf()["column_name"].tolist()
cbo_col = "cbo" if "cbo" in cols else None

if cbo_col is None:
    raise RuntimeError("Não encontrei a coluna CBO na tabela odontologia_vinculos.")

df = con.execute(f"""
    SELECT
        CAST({cbo_col} AS VARCHAR) AS cbo_raw,
        COUNT(*) AS vinculos,
        COUNT(DISTINCT ano) AS anos_com_dado,
        MIN(ano) AS primeiro_ano,
        MAX(ano) AS ultimo_ano
    FROM odontologia_vinculos
    GROUP BY 1
    ORDER BY vinculos DESC
""").fetchdf()

con.close()

df["cbo"] = df["cbo_raw"].map(only_digits)

rows = []

for _, r in df.iterrows():
    cbo = r["cbo"]

    if cbo in MAPA_BASE:
        nome, grupo, familia = MAPA_BASE[cbo]
        status = "mapeado"
    elif cbo.startswith("2232"):
        nome = f"Cirurgião-dentista — CBO {cbo}"
        grupo = "Cirurgiões-dentistas"
        familia = "Especialidade odontológica não classificada no mapa"
        status = "revisar_nome"
    elif cbo.startswith("3224"):
        nome = f"Ocupação auxiliar odontológica — CBO {cbo}"
        grupo = "Equipe auxiliar odontológica"
        familia = "Auxiliares, técnicos e prótese dentária"
        status = "revisar_nome"
    else:
        nome = f"Ocupação relacionada presente na base — CBO {cbo}"
        grupo = "Outras ocupações presentes no recorte odontológico"
        familia = "Revisar pertinência odontológica"
        status = "revisar_pertinencia"

    rows.append({
        "cbo": cbo,
        "cbo_nome": nome,
        "grupo_ocupacional": grupo,
        "familia_especialidade": familia,
        "status_mapeamento": status,
        "vinculos": int(r["vinculos"]),
        "anos_com_dado": int(r["anos_com_dado"]),
        "primeiro_ano": int(r["primeiro_ano"]),
        "ultimo_ano": int(r["ultimo_ano"]),
    })

out = pd.DataFrame(rows).sort_values(["grupo_ocupacional", "familia_especialidade", "cbo"])
OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, sep=";", index=False, encoding="utf-8-sig")

print("Mapa CBO gerado em:")
print(OUT)
print()
print("Total de CBOs no banco:", len(out))
print()
print("Resumo por grupo:")
print(out.groupby("grupo_ocupacional")["cbo"].count().sort_values(ascending=False).to_string())
print()
print("CBOs a revisar:")
print(out[out["status_mapeamento"] != "mapeado"][["cbo", "cbo_nome", "grupo_ocupacional", "vinculos", "status_mapeamento"]].head(50).to_string(index=False))
