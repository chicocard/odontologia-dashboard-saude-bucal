
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import duckdb
import pandas as pd


PROJECT_DIR = Path(r"C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3")
DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
TABLE = "odontologia_vinculos"

TERRITORY_CANDIDATES = [
    PROJECT_DIR / "reference" / "tabela_regioes(1).csv",
    PROJECT_DIR / "reference" / "tabela_regioes.csv",
    PROJECT_DIR / "tabela_regioes(1).csv",
    PROJECT_DIR / "tabela_regioes.csv",
]

OUT_XLSX = PROJECT_DIR / "diagnostico_discrepancia_taxas.xlsx"


def pick(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def digits_only(x: Any) -> str:
    if pd.isna(x):
        return ""
    return re.sub(r"[^0-9]", "", str(x))


def normalize_territory_code(x: Any) -> str:
    d = digits_only(x)
    if not d:
        return ""
    if len(d) >= 7 and d.startswith("0"):
        return d[-6:]
    if len(d) >= 7:
        return d[:6]
    if len(d) >= 6:
        return d[-6:]
    return d.zfill(6)


def candidates(raw: Any) -> list[str]:
    d = digits_only(raw)
    if not d:
        return []

    s = d.lstrip("0")
    out: list[str] = []

    def add(x: str):
        if x and len(x) == 6 and x not in out:
            out.append(x)

    if len(d) == 6:
        add(d)
    if len(d) < 6:
        add(d.zfill(6))
    if len(d) >= 6:
        add(d[:6])
        add(d[-6:])

    if len(s) == 6:
        add(s)
    if len(s) < 6 and s:
        add(s.zfill(6))
    if len(s) >= 6:
        add(s[:6])
        add(s[-6:])

    return out


def zeroaware(raw: Any) -> str:
    d = digits_only(raw)
    if not d:
        return ""
    if len(d) < 6:
        return d.zfill(6)
    if len(d) == 6:
        return d
    if len(d) == 7 and d.startswith("0"):
        return d[-6:]
    if len(d) == 7:
        return d[:6]
    s = d.lstrip("0")
    if len(s) == 6:
        return s
    if len(s) == 7 and s.startswith("0"):
        return s[-6:]
    if len(s) == 7:
        return s[:6]
    return d[:6]


def best_valid(raw: Any, valid_codes: set[str]) -> str:
    for c in candidates(raw):
        if c in valid_codes:
            return c
    cs = candidates(raw)
    return cs[0] if cs else ""


def load_territory() -> tuple[pd.DataFrame, Path]:
    found = None
    for p in TERRITORY_CANDIDATES:
        if p.exists():
            found = p
            break

    if found is None:
        raise FileNotFoundError(
            "Não encontrei tabela_regioes(1).csv em reference/. "
            f"Locais testados: {[str(p) for p in TERRITORY_CANDIDATES]}"
        )

    df = pd.read_csv(found, sep=";", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    code_col = pick(df.columns.tolist(), ["cod_municipio", "co_municipio", "codigo_municipio"])
    pop_col = pick(df.columns.tolist(), ["populacao_ibge_2022", "populacao", "população"])
    uf_col = pick(df.columns.tolist(), ["sg_uf", "uf_sigla", "uf"])
    mun_col = pick(df.columns.tolist(), ["no_municipio", "municipio", "município"])
    reg_col = pick(df.columns.tolist(), ["regiao_de_saude", "região_de_saude", "regiao_saude"])
    macro_col = pick(df.columns.tolist(), ["macrorregiao_de_saude", "macrorregião_de_saude", "macro"])

    if code_col is None:
        raise RuntimeError("Tabela de regiões sem coluna de código municipal.")

    out = pd.DataFrame()
    out["cod_municipio"] = df[code_col].apply(normalize_territory_code)
    out["uf"] = df[uf_col].astype(str) if uf_col else ""
    out["municipio"] = df[mun_col].astype(str) if mun_col else out["cod_municipio"]
    out["regiao_saude"] = df[reg_col].astype(str) if reg_col else ""
    out["macrorregiao_saude"] = df[macro_col].astype(str) if macro_col else ""

    if pop_col:
        pop = df[pop_col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        out["populacao"] = pd.to_numeric(pop, errors="coerce")
    else:
        out["populacao"] = pd.NA

    out = out.drop_duplicates("cod_municipio").copy()
    out = out[out["cod_municipio"].str.len() == 6].copy()

    return out, found


def main():
    print("=== DIAGNÓSTICO DA DISCREPÂNCIA DAS TAXAS ===")
    print("Projeto:", PROJECT_DIR)
    print("Banco:", DB_PATH)

    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)

    territory, territory_path = load_territory()
    valid_codes = set(territory["cod_municipio"].astype(str).tolist())

    print("Tabela territorial:", territory_path)
    print("Municípios na tabela territorial:", len(valid_codes))

    con = duckdb.connect(str(DB_PATH), read_only=True)
    cols = con.execute(f"DESCRIBE {TABLE}").fetchdf()["column_name"].tolist()

    ano_col = pick(cols, ["ano"])
    municipio_col = pick(cols, ["municipio", "co_municipio", "cod_municipio", "Município"])
    cbo_col = pick(cols, ["cbo", "cbo_ocupacao_2002", "CBO Ocupação 2002"])

    if not ano_col or not municipio_col:
        raise RuntimeError(f"Colunas essenciais não encontradas. ano={ano_col}, municipio={municipio_col}")

    print("Coluna ano:", ano_col)
    print("Coluna município:", municipio_col)
    print("Coluna CBO:", cbo_col)

    totals = con.execute(f"""
        SELECT CAST("{ano_col}" AS INTEGER) AS ano, COUNT(*) AS vinculos_banco
        FROM {TABLE}
        GROUP BY 1
        ORDER BY 1
    """).fetchdf()

    raw = con.execute(f"""
        SELECT
            CAST("{ano_col}" AS INTEGER) AS ano,
            CAST("{municipio_col}" AS VARCHAR) AS municipio_raw,
            COUNT(*) AS vinculos
        FROM {TABLE}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchdf()

    raw["digits"] = raw["municipio_raw"].map(digits_only)
    raw["len_digits"] = raw["digits"].str.len()

    raw["cod_raw6"] = raw["digits"].where(raw["digits"].str.len() == 6, "")
    raw["cod_first6"] = raw["digits"].str[:6].where(raw["digits"].str.len() >= 6, raw["digits"].str.zfill(6))
    raw["cod_last6"] = raw["digits"].str[-6:].where(raw["digits"].str.len() >= 6, raw["digits"].str.zfill(6))
    raw["cod_zeroaware"] = raw["municipio_raw"].map(zeroaware)
    raw["cod_best_valid"] = raw["municipio_raw"].map(lambda x: best_valid(x, valid_codes))
    raw["has_any_valid_candidate"] = raw["municipio_raw"].map(lambda x: any(c in valid_codes for c in candidates(x)))

    strategies = {
        "raw6": "cod_raw6",
        "first6": "cod_first6",
        "last6": "cod_last6",
        "zeroaware": "cod_zeroaware",
        "best_valid": "cod_best_valid",
    }

    strategy_rows = []
    for name, col in strategies.items():
        tmp = raw.copy()
        tmp["matched"] = tmp[col].isin(valid_codes)
        res = (
            tmp.groupby("ano", as_index=False)
            .agg(
                vinculos_estrategia=("vinculos", "sum"),
                vinculos_matched=("vinculos", lambda s: tmp.loc[s.index, "vinculos"][tmp.loc[s.index, "matched"]].sum()),
                codigos_distintos=(col, "nunique"),
                codigos_matched=(col, lambda s: s[tmp.loc[s.index, "matched"]].nunique()),
            )
        )
        res["estrategia"] = name
        res["percentual_matched"] = res["vinculos_matched"] / res["vinculos_estrategia"].replace(0, pd.NA) * 100
        strategy_rows.append(res)

    strategy_diag = pd.concat(strategy_rows, ignore_index=True)
    strategy_diag = strategy_diag[
        ["ano", "estrategia", "vinculos_estrategia", "vinculos_matched", "percentual_matched", "codigos_distintos", "codigos_matched"]
    ].sort_values(["ano", "estrategia"])

    any_valid = (
        raw.groupby("ano", as_index=False)
        .agg(
            vinculos_total=("vinculos", "sum"),
            vinculos_com_algum_candidato_valido=("vinculos", lambda s: raw.loc[s.index, "vinculos"][raw.loc[s.index, "has_any_valid_candidate"]].sum()),
            codigos_raw_distintos=("municipio_raw", "nunique"),
        )
    )
    any_valid["percentual_com_algum_candidato_valido"] = (
        any_valid["vinculos_com_algum_candidato_valido"] / any_valid["vinculos_total"].replace(0, pd.NA) * 100
    )

    format_profile = (
        raw.groupby(["ano", "len_digits"], as_index=False)
        .agg(
            vinculos=("vinculos", "sum"),
            codigos_raw_distintos=("municipio_raw", "nunique"),
            exemplo_min=("municipio_raw", "min"),
            exemplo_max=("municipio_raw", "max"),
        )
        .sort_values(["ano", "len_digits"])
    )

    raw["matched_best"] = raw["cod_best_valid"].isin(valid_codes)
    unmatched = (
        raw[~raw["matched_best"]]
        .sort_values(["ano", "vinculos"], ascending=[True, False])
        .groupby("ano")
        .head(30)
        [["ano", "municipio_raw", "digits", "len_digits", "vinculos", "cod_best_valid"]]
        .copy()
    )

    # Painel municipal com melhor estratégia validada.
    matched_counts = raw[raw["cod_best_valid"].isin(valid_codes)].copy()
    matched_counts = (
        matched_counts.groupby(["ano", "cod_best_valid"], as_index=False)["vinculos"]
        .sum()
        .rename(columns={"cod_best_valid": "cod_municipio"})
    )

    panel = matched_counts.merge(territory, on="cod_municipio", how="left")
    panel["taxa_10000"] = panel["vinculos"] / panel["populacao"] * 10000

    taxa_summary = (
        panel.groupby("ano", as_index=False)
        .agg(
            vinculos_integrados=("vinculos", "sum"),
            municipios_integrados=("cod_municipio", "nunique"),
            populacao_integrada=("populacao", "sum"),
            taxa_agregada_10000=("taxa_10000", "mean"),
            taxa_mediana_municipal_10000=("taxa_10000", "median"),
            p25=("taxa_10000", lambda x: x.quantile(0.25)),
            p75=("taxa_10000", lambda x: x.quantile(0.75)),
            maximo=("taxa_10000", "max"),
        )
        .merge(totals, on="ano", how="left")
    )
    taxa_summary["percentual_integrado"] = taxa_summary["vinculos_integrados"] / taxa_summary["vinculos_banco"].replace(0, pd.NA) * 100
    taxa_summary["taxa_agregada_correta_10000"] = taxa_summary["vinculos_integrados"] / taxa_summary["populacao_integrada"] * 10000

    if cbo_col:
        top_cbo = con.execute(f"""
            SELECT
                CAST("{ano_col}" AS INTEGER) AS ano,
                CAST("{cbo_col}" AS VARCHAR) AS cbo,
                COUNT(*) AS vinculos
            FROM {TABLE}
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
        """).fetchdf()
        top_cbo = top_cbo.groupby("ano").head(30)
    else:
        top_cbo = pd.DataFrame()

    print("\n--- Totais no banco ---")
    print(totals.to_string(index=False))

    print("\n--- Match por estratégia ---")
    print(strategy_diag.to_string(index=False))

    print("\n--- Algum candidato válido ---")
    print(any_valid.to_string(index=False))

    print("\n--- Resumo das taxas usando melhor código validado ---")
    print(taxa_summary.to_string(index=False))

    print("\nGravando Excel:", OUT_XLSX)
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        totals.to_excel(writer, index=False, sheet_name="totais_banco")
        strategy_diag.to_excel(writer, index=False, sheet_name="match_estrategias")
        any_valid.to_excel(writer, index=False, sheet_name="algum_candidato_valido")
        format_profile.to_excel(writer, index=False, sheet_name="perfil_codigos")
        unmatched.to_excel(writer, index=False, sheet_name="nao_integrados_top")
        taxa_summary.to_excel(writer, index=False, sheet_name="resumo_taxas")
        panel.sort_values(["ano", "taxa_10000"], ascending=[True, False]).to_excel(writer, index=False, sheet_name="municipios_taxas")
        top_cbo.to_excel(writer, index=False, sheet_name="top_cbo")

    print("\nCONCLUSÃO AUTOMÁTICA:")
    min_pct = taxa_summary["percentual_integrado"].min()
    if pd.notna(min_pct) and min_pct < 95:
        print(f"- A integração município-população ainda está incompleta. Menor percentual integrado: {min_pct:.2f}%.")
        print("- Veja as abas 'match_estrategias', 'perfil_codigos' e 'nao_integrados_top'.")
    else:
        print("- A integração município-população parece alta. Se a discrepância persistir, o problema não é apenas o código municipal.")
        print("- Nesse caso, verificar: filtro de CBO, composição por CBO, população usada e duplicidade/alteração na seleção de 2019.")

    con.close()


if __name__ == "__main__":
    main()
