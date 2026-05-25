
from __future__ import annotations

from pathlib import Path
import re

import duckdb
import pandas as pd


DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
PROJECT_DIR = Path(r"C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3")
OUT = PROJECT_DIR / "reference" / "cbo_odontologia_mapa.csv"

MAPA_BASE = {
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
    "322405": ("Técnico em saúde bucal", "Equipe auxiliar odontológica", "Técnico em saúde bucal"),
    "322410": ("Protético dentário", "Equipe auxiliar odontológica", "Prótese dentária"),
    "322415": ("Auxiliar em saúde bucal", "Equipe auxiliar odontológica", "Auxiliar em saúde bucal"),
    "322420": ("Auxiliar de prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"),
    "322425": ("Técnico em prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"),
    "322430": ("Auxiliar/técnico de apoio em saúde bucal", "Equipe auxiliar odontológica", "Auxiliar em saúde bucal"),
}


def only_digits(x) -> str:
    return re.sub(r"[^0-9]", "", str(x)) if x is not None else ""


def classify_cbo(cbo: str):
    if cbo in MAPA_BASE:
        nome, grupo, familia = MAPA_BASE[cbo]
        return nome, grupo, familia, "mapeado"

    if cbo.startswith("2232"):
        return (
            f"Cirurgião-dentista — CBO {cbo}",
            "Cirurgiões-dentistas",
            "Especialidade odontológica não classificada no mapa",
            "revisar_nome",
        )

    if cbo.startswith("3224"):
        return (
            f"Ocupação auxiliar odontológica — CBO {cbo}",
            "Equipe auxiliar odontológica",
            "Auxiliares, técnicos e prótese dentária",
            "revisar_nome",
        )

    return (
        f"Ocupação relacionada presente na base — CBO {cbo}",
        "Outras ocupações presentes no recorte odontológico",
        "Revisar pertinência odontológica",
        "revisar_pertinencia",
    )


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    cols = con.execute("DESCRIBE odontologia_vinculos").fetchdf()["column_name"].tolist()
    if "cbo" not in cols:
        raise RuntimeError("A tabela odontologia_vinculos não possui coluna 'cbo'.")

    df = con.execute("""
        SELECT
            CAST(cbo AS VARCHAR) AS cbo_raw,
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
    for _, row in df.iterrows():
        cbo = row["cbo"]
        nome, grupo, familia, status = classify_cbo(cbo)
        rows.append(
            {
                "cbo": cbo,
                "cbo_nome": nome,
                "grupo_ocupacional": grupo,
                "familia_especialidade": familia,
                "status_mapeamento": status,
                "vinculos": int(row["vinculos"]),
                "anos_com_dado": int(row["anos_com_dado"]),
                "primeiro_ano": int(row["primeiro_ano"]),
                "ultimo_ano": int(row["ultimo_ano"]),
            }
        )

    out = pd.DataFrame(rows).sort_values(
        ["grupo_ocupacional", "familia_especialidade", "cbo"]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, sep=";", index=False, encoding="utf-8-sig")

    print("Mapa gerado:", OUT)
    print("CBOs encontrados:", len(out))
    print()
    print("Resumo por grupo:")
    print(out.groupby("grupo_ocupacional")["cbo"].count().sort_values(ascending=False).to_string())
    print()
    print("CBOs a revisar:")
    revisar = out[out["status_mapeamento"] != "mapeado"]
    if revisar.empty:
        print("Nenhum.")
    else:
        print(revisar[["cbo", "cbo_nome", "grupo_ocupacional", "vinculos", "status_mapeamento"]].head(100).to_string(index=False))


if __name__ == "__main__":
    main()
