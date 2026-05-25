
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
TABLE = "odontologia_vinculos"
APP_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = APP_DIR / "reference"

TERRITORY_CANDIDATES = [
    REFERENCE_DIR / "tabela_regioes(1).csv",
    REFERENCE_DIR / "tabela_regioes.csv",
    APP_DIR / "tabela_regioes(1).csv",
    APP_DIR / "tabela_regioes.csv",
]

POPULATION_CANDIDATES = [
    REFERENCE_DIR / "populacao_tcu_municipios.csv",
    APP_DIR / "populacao_tcu_municipios.csv",
]

CBO_MAP_CANDIDATES = [
    REFERENCE_DIR / "cbo_odontologia_mapa.csv",
    APP_DIR / "cbo_odontologia_mapa.csv",
]

st.set_page_config(
    page_title="OdontoWorkforce Brasil — V4",
    page_icon="🦷",
    layout="wide",
)

# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.9rem;
        padding-bottom: 2.4rem;
        max-width: 1580px;
    }
    .ow-title {
        font-size: 2.45rem;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: -0.045em;
        margin-bottom: 0.08rem;
    }
    .ow-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.15rem;
    }
    .ow-note {
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        color: #334155;
        padding: 0.85rem 1rem;
        border-radius: 1rem;
        margin: 0.75rem 0 1rem 0;
    }
    .ow-card {
        border: 1px solid #e8eef5;
        background: #ffffff;
        border-radius: 1rem;
        padding: 0.9rem 1rem;
        box-shadow: 0 3px 14px rgba(15,23,42,0.045);
        margin-bottom: 0.8rem;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #e6edf5;
        padding: 1rem;
        border-radius: 1.05rem;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.055);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.62rem;
        font-weight: 850;
    }
    .stTabs [data-baseweb="tab-list"] { gap: .35rem; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        padding: .42rem .75rem;
        background-color: #f8fafc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# RÓTULOS E DICIONÁRIOS
# ============================================================

COLUMN_LABELS = {
    "ano": "Ano",
    "vinculos": "Vínculos",
    "vinculo": "Vínculos",
    "municipios": "Municípios",
    "municipios_com_vinculo": "Municípios com vínculo",
    "ocupacoes_cbo": "Ocupações CBO",
    "cod_municipio": "Código IBGE do município",
    "municipio": "Município",
    "municipio_label": "Município",
    "no_municipio": "Município",
    "sg_uf": "UF",
    "uf": "Estado",
    "regiao_pais": "Grande região",
    "regiao_de_saude": "Região de saúde",
    "macrorregiao_de_saude": "Macrorregião de saúde",
    "populacao": "População",
    "populacao_usada": "População usada no denominador",
    "ano_populacao_usado": "Ano da população usada",
    "tipo_populacao": "Tipo do denominador populacional",
    "taxa": "Taxa per capita",
    "taxa_municipal": "Taxa municipal",
    "taxa_regional": "Taxa regional",
    "taxa_macro": "Taxa macrorregional",
    "cbo": "CBO",
    "cbo_nome": "Especialidade / ocupação",
    "cbo_label": "Especialidade / ocupação",
    "grupo_cbo": "Grupo ocupacional",
    "familia_cbo": "Família de especialidade",
    "especialidade_macro": "Macrogrupo da especialidade",
    "setor": "Setor / natureza do vínculo",
    "sexo": "Sexo",
    "sexo_nome": "Sexo",
    "raca_cor": "Raça/cor",
    "raca_cor_nome": "Raça/cor",
    "registros": "Registros",
    "validos": "Registros válidos",
    "registros_validos": "Registros válidos",
    "remuneracao_media": "Remuneração média",
    "remuneracao_mediana": "Remuneração mediana",
    "p25": "Percentil 25",
    "p75": "Percentil 75",
    "idade_media": "Idade média",
    "horas_semanais_media": "Horas semanais médias",
}

SEX_LABELS = {
    "1": "Masculino",
    "2": "Feminino",
    "9": "Ignorado / não informado",
    "M": "Masculino",
    "F": "Feminino",
}

RACE_LABELS = {
    "1": "Indígena",
    "2": "Branca",
    "4": "Preta",
    "6": "Amarela",
    "8": "Parda",
    "9": "Não identificada",
}

# Mapa interno para CBOs odontológicos mais frequentes. Caso o banco já tenha descrição,
# a descrição do banco prevalece. Códigos não mapeados aparecem como "CBO 999999".
CBO_FALLBACK = {
    "223204": ("Cirurgião-dentista — auditor", "Cirurgiões-dentistas", "Gestão, auditoria e perícia"),
    "223208": ("Cirurgião-dentista — clínico geral", "Cirurgiões-dentistas", "Clínica odontológica geral"),
    "223212": ("Cirurgião-dentista — endodontista", "Cirurgiões-dentistas", "Especialidades clínicas"),
    "223216": ("Cirurgião-dentista — epidemiologista", "Cirurgiões-dentistas", "Saúde coletiva e epidemiologia"),
    "223220": ("Cirurgião-dentista — estomatologista", "Cirurgiões-dentistas", "Diagnóstico e patologia bucal"),
    "223224": ("Cirurgião-dentista — implantodontista", "Cirurgiões-dentistas", "Reabilitação oral e prótese"),
    "223228": ("Cirurgião-dentista — odontogeriatra", "Cirurgiões-dentistas", "Ciclos de vida e cuidado especializado"),
    "223232": ("Cirurgião-dentista — odontolegista", "Cirurgiões-dentistas", "Gestão, auditoria e perícia"),
    "223236": ("Cirurgião-dentista — odontopediatra", "Cirurgiões-dentistas", "Ciclos de vida e cuidado especializado"),
    "223240": ("Cirurgião-dentista — ortopedista/ortodontista", "Cirurgiões-dentistas", "Ortodontia e ortopedia facial"),
    "223244": ("Cirurgião-dentista — patologista bucal", "Cirurgiões-dentistas", "Diagnóstico e patologia bucal"),
    "223248": ("Cirurgião-dentista — periodontista", "Cirurgiões-dentistas", "Especialidades clínicas"),
    "223252": ("Cirurgião-dentista — protesista bucomaxilofacial", "Cirurgiões-dentistas", "Reabilitação oral e prótese"),
    "223256": ("Cirurgião-dentista — protesista", "Cirurgiões-dentistas", "Reabilitação oral e prótese"),
    "223260": ("Cirurgião-dentista — radiologista", "Cirurgiões-dentistas", "Diagnóstico e imagem"),
    "223264": ("Cirurgião-dentista — traumatologista bucomaxilofacial", "Cirurgiões-dentistas", "Cirurgia e traumatologia"),
    "223268": ("Cirurgião-dentista — saúde coletiva", "Cirurgiões-dentistas", "Saúde coletiva e epidemiologia"),
    "322405": ("Técnico em saúde bucal", "Técnicos e auxiliares em saúde bucal", "Equipe auxiliar odontológica"),
    "322410": ("Protético dentário", "Técnicos e auxiliares em saúde bucal", "Prótese dentária"),
    "322415": ("Auxiliar em saúde bucal", "Técnicos e auxiliares em saúde bucal", "Equipe auxiliar odontológica"),
    "322420": ("Auxiliar de prótese dentária", "Técnicos e auxiliares em saúde bucal", "Prótese dentária"),
    "322425": ("Técnico em prótese dentária", "Técnicos e auxiliares em saúde bucal", "Prótese dentária"),
}

# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def q(col: str) -> str:
    return '"' + str(col).replace('"', '""') + '"'


def lit(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def fmt_int(x: Any) -> str:
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return "0"


def fmt_float(x: Any, decimals: int = 2) -> str:
    try:
        return f"{float(x):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def normalize_digits(value: Any, width: int = 6) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return ""
    return digits[-width:].zfill(width)


def connect(read_only: bool = True):
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def sql_df(sql: str) -> pd.DataFrame:
    con = connect(read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def plot(fig):
    fig.update_layout(
        margin=dict(l=20, r=20, t=58, b=40),
        legend_title_text="",
        font=dict(size=13),
    )
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def label_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    return df.rename(columns={c: COLUMN_LABELS.get(c, c.replace("_", " ").title()) for c in df.columns})


def show_table(df: pd.DataFrame, height: int | str | None = None, max_rows: int | None = None):
    """
    Exibe DataFrame no Streamlit com:
    - nomes amig?veis de colunas, se a fun??o friendly_dataframe existir;
    - remo??o autom?tica de nomes duplicados de colunas;
    - compatibilidade com vers?es novas do Streamlit, que n?o aceitam height=None.
    """
    display = df.copy()

    formatter = globals().get("friendly_dataframe")
    if callable(formatter):
        try:
            display = formatter(display)
        except Exception:
            display = df.copy()

    if max_rows is not None:
        display = display.head(max_rows).copy()

    # PyArrow/Streamlit n?o aceita nomes duplicados de colunas.
    seen = {}
    new_cols = []

    for col in display.columns:
        base = str(col)

        if base in seen:
            seen[base] += 1
            new_cols.append(f"{base} ({seen[base] + 1})")
        else:
            seen[base] = 0
            new_cols.append(base)

    display.columns = new_cols

    kwargs = {"hide_index": True}

    if height is not None:
        kwargs["height"] = height

    try:
        st.dataframe(display, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(display, use_container_width=True, **kwargs)


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = name[:31].replace("/", "_").replace("\\", "_")
            label_df(df).to_excel(writer, index=False, sheet_name=safe)
    return output.getvalue()


def download_buttons(df: pd.DataFrame, base_name: str, sheets: dict[str, pd.DataFrame] | None = None):
    c1, c2 = st.columns(2)
    display_df = label_df(df)
    with c1:
        st.download_button(
            "⬇️ Baixar CSV",
            data=display_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{base_name}.csv",
            mime="text/csv",
            key=f"{base_name}_csv",
            width="stretch",
        )
    with c2:
        st.download_button(
            "⬇️ Baixar Excel",
            data=excel_bytes(sheets if sheets else {"dados": df}),
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{base_name}_xlsx",
            width="stretch",
        )


def pick(cols: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def numeric_expr(col: str) -> str:
    return f"""
    COALESCE(
        TRY_CAST({q(col)} AS DOUBLE),
        TRY_CAST(REPLACE(CAST({q(col)} AS VARCHAR), ',', '.') AS DOUBLE),
        TRY_CAST(REPLACE(REPLACE(CAST({q(col)} AS VARCHAR), '.', ''), ',', '.') AS DOUBLE)
    )
    """


def code_key_expr(col: str, width: int = 6) -> str:
    return f"""
    RIGHT(
        '{'0' * width}' || REGEXP_REPLACE(CAST({q(col)} AS VARCHAR), '[^0-9]', '', 'g'),
        {width}
    )
    """


def mun_key_expr(col: str) -> str:
    return code_key_expr(col, 6)


def cbo_key_expr(col: str) -> str:
    return code_key_expr(col, 6)


def cbo_fallback_name(cbo: Any) -> str:
    code = normalize_digits(cbo, 6)
    if code in CBO_FALLBACK:
        return CBO_FALLBACK[code][0]
    if code.startswith("2232"):
        return f"Cirurgião-dentista — CBO {code}"
    if code.startswith("3224"):
        return f"Técnico/auxiliar de odontologia — CBO {code}"
    return f"CBO {code}" if code else "CBO não informado"


def cbo_group(cbo: Any) -> str:
    code = normalize_digits(cbo, 6)
    if code in CBO_FALLBACK:
        return CBO_FALLBACK[code][1]
    if code.startswith("2232"):
        return "Cirurgiões-dentistas"
    if code.startswith("3224"):
        return "Técnicos e auxiliares em saúde bucal"
    return "Outras ocupações na base"


def cbo_family(cbo: Any) -> str:
    code = normalize_digits(cbo, 6)
    if code in CBO_FALLBACK:
        return CBO_FALLBACK[code][2]
    if code.startswith("2232"):
        return "Outras especialidades odontológicas"
    if code.startswith("3224"):
        return "Equipe auxiliar odontológica"
    return "Outras ocupações"


def value_label(value: Any, mapping: dict[str, str]) -> str:
    raw = "" if pd.isna(value) else str(value).strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if raw in mapping:
        return mapping[raw]
    if digits in mapping:
        return mapping[digits]
    return raw if raw else "Não informado"


@st.cache_data(show_spinner=False)
def get_table_columns() -> list[str]:
    con = connect(read_only=True)
    try:
        tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
        if TABLE not in tables:
            return []
        return con.execute(f"DESCRIBE {TABLE}").fetchdf()["column_name"].tolist()
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def get_years(ano_col: str) -> list[int]:
    df = sql_df(f"""
        SELECT DISTINCT CAST({q(ano_col)} AS INTEGER) AS ano
        FROM {TABLE}
        WHERE {q(ano_col)} IS NOT NULL
        ORDER BY 1
    """)
    return df["ano"].dropna().astype(int).tolist()


@st.cache_data(show_spinner=False)
def load_external_cbo_map() -> pd.DataFrame:
    for path in CBO_MAP_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path, sep=";", dtype=str)
            df.columns = [c.strip() for c in df.columns]
            if "cbo" in df.columns:
                df["cbo"] = df["cbo"].map(lambda x: normalize_digits(x, 6))
                return df.drop_duplicates("cbo")
    return pd.DataFrame(columns=["cbo", "cbo_nome", "grupo_cbo", "familia_cbo"])


@st.cache_data(show_spinner=False)
def get_cbo_options(cbo_col: str, cbo_desc_col: str | None = None) -> pd.DataFrame:
    key = cbo_key_expr(cbo_col)
    if cbo_desc_col:
        name_expr = f"ANY_VALUE(CAST({q(cbo_desc_col)} AS VARCHAR)) AS cbo_nome_db,"
    else:
        name_expr = "CAST(NULL AS VARCHAR) AS cbo_nome_db,"

    df = sql_df(f"""
        SELECT
            {key} AS cbo,
            {name_expr}
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
        FROM {TABLE}
        WHERE {q(cbo_col)} IS NOT NULL
        GROUP BY 1
        ORDER BY vinculos DESC
    """)

    ext = load_external_cbo_map()
    if not ext.empty:
        df = df.merge(ext, on="cbo", how="left")
    else:
        df["cbo_nome"] = None
        df["grupo_cbo"] = None
        df["familia_cbo"] = None

    df["cbo_nome"] = df.apply(
        lambda r: r.get("cbo_nome") if pd.notna(r.get("cbo_nome")) and str(r.get("cbo_nome")).strip() else (
            r.get("cbo_nome_db") if pd.notna(r.get("cbo_nome_db")) and str(r.get("cbo_nome_db")).strip() else cbo_fallback_name(r["cbo"])
        ),
        axis=1,
    )
    df["grupo_cbo"] = df.apply(
        lambda r: r.get("grupo_cbo") if pd.notna(r.get("grupo_cbo")) and str(r.get("grupo_cbo")).strip() else cbo_group(r["cbo"]),
        axis=1,
    )
    df["familia_cbo"] = df.apply(
        lambda r: r.get("familia_cbo") if pd.notna(r.get("familia_cbo")) and str(r.get("familia_cbo")).strip() else cbo_family(r["cbo"]),
        axis=1,
    )
    df["label"] = df["cbo_nome"].astype(str) + " — " + df["cbo"].astype(str) + " (" + df["vinculos"].map(fmt_int) + ")"
    return df[["cbo", "cbo_nome", "grupo_cbo", "familia_cbo", "vinculos", "municipios", "label"]].sort_values("vinculos", ascending=False)


def find_file(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_territory_from_path(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    try:
        df = pd.read_csv(path, sep=";", dtype={"cod_municipio": str})
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", dtype={"cod_municipio": str})

    df.columns = [c.strip() for c in df.columns]
    required = [
        "sg_uf", "uf", "cod_municipio", "no_municipio",
        "regiao_de_saude", "macrorregiao_de_saude", "populacao_ibge_2022",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na tabela de regiões: {missing}")

    df["cod_municipio"] = df["cod_municipio"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    df["populacao_ibge_2022"] = pd.to_numeric(df["populacao_ibge_2022"], errors="coerce").fillna(0)
    df["municipio_nome_limpo"] = df["no_municipio"].astype(str).str.replace(r"^[A-Z]{2}\s*-\s*", "", regex=True).str.title()
    df["municipio_label"] = df["sg_uf"].astype(str) + " — " + df["municipio_nome_limpo"].astype(str)
    return df.drop_duplicates("cod_municipio").copy()


def load_territory() -> tuple[pd.DataFrame | None, str]:
    found = find_file(TERRITORY_CANDIDATES)
    if found:
        return load_territory_from_path(str(found)), str(found)
    return None, ""


@st.cache_data(show_spinner=False)
def load_population_municipal_from_path(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    try:
        df = pd.read_csv(path, sep=";", dtype={"cod_municipio": str})
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", dtype={"cod_municipio": str})
    df.columns = [c.strip() for c in df.columns]

    expected = {"ano", "cod_municipio", "populacao"}
    if not expected.issubset(set(df.columns)):
        return pd.DataFrame(columns=["ano", "cod_municipio", "populacao", "fonte_populacao"])

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["cod_municipio"] = df["cod_municipio"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    if "fonte_populacao" not in df.columns:
        df["fonte_populacao"] = "População municipal"
    return df.dropna(subset=["ano", "cod_municipio", "populacao"]).drop_duplicates(["ano", "cod_municipio"])


def load_population_municipal(territory: pd.DataFrame | None) -> tuple[pd.DataFrame, str]:
    found = find_file(POPULATION_CANDIDATES)
    if found:
        return load_population_municipal_from_path(str(found)), str(found)
    if territory is not None:
        df = territory[["cod_municipio", "sg_uf", "municipio_nome_limpo", "populacao_ibge_2022"]].copy()
        df["ano"] = 2022
        df = df.rename(columns={"populacao_ibge_2022": "populacao", "municipio_nome_limpo": "municipio_nome"})
        df["fonte_populacao"] = "IBGE 2022 da tabela de regiões"
        return df[["ano", "cod_municipio", "sg_uf", "municipio_nome", "populacao", "fonte_populacao"]], "tabela_regioes(1).csv"
    return pd.DataFrame(columns=["ano", "cod_municipio", "populacao", "fonte_populacao"]), ""


def complete_municipal_panel(counts: pd.DataFrame, terr: pd.DataFrame, pop: pd.DataFrame, selected_years: list[int], tax_base: int) -> pd.DataFrame:
    territory_base = terr[[
        "cod_municipio", "municipio_label", "no_municipio", "sg_uf", "uf", "regiao_pais",
        "cod_regiao_de_saude", "regiao_de_saude", "cod_macrorregiao_de_saude", "macrorregiao_de_saude",
        "populacao_ibge_2022",
    ]].drop_duplicates("cod_municipio").copy()

    grid = pd.MultiIndex.from_product([selected_years, territory_base["cod_municipio"].tolist()], names=["ano", "cod_municipio"]).to_frame(index=False)
    panel = grid.merge(territory_base, on="cod_municipio", how="left")

    counts2 = counts.copy()
    if not counts2.empty:
        counts2["cod_municipio"] = counts2["cod_municipio"].astype(str).str[-6:].str.zfill(6)
        panel = panel.merge(counts2, on=["ano", "cod_municipio"], how="left")
    else:
        panel["vinculos"] = 0
        panel["ocupacoes_cbo"] = 0

    panel["vinculos"] = panel["vinculos"].fillna(0).astype(int)
    panel["ocupacoes_cbo"] = panel["ocupacoes_cbo"].fillna(0).astype(int)

    pop2 = pop.copy()
    if pop2.empty:
        pop2 = territory_base[["cod_municipio", "populacao_ibge_2022"]].copy()
        pop2["ano"] = 2022
        pop2 = pop2.rename(columns={"populacao_ibge_2022": "populacao"})
        pop2["fonte_populacao"] = "IBGE 2022 da tabela de regiões"

    pop2["ano"] = pd.to_numeric(pop2["ano"], errors="coerce").astype("Int64")
    pop2["cod_municipio"] = pop2["cod_municipio"].astype(str).str[-6:].str.zfill(6)
    pop2["populacao"] = pd.to_numeric(pop2["populacao"], errors="coerce")
    if "fonte_populacao" not in pop2.columns:
        pop2["fonte_populacao"] = "População municipal"
    pop2 = pop2.dropna(subset=["ano", "cod_municipio", "populacao"]).drop_duplicates(["ano", "cod_municipio"])

    exact = pop2.rename(columns={"populacao": "populacao_exata", "fonte_populacao": "fonte_populacao_exata"})
    panel = panel.merge(exact[["ano", "cod_municipio", "populacao_exata", "fonte_populacao_exata"]], on=["ano", "cod_municipio"], how="left")

    # Fallback por ano mais próximo dentro do mesmo município.
    pop_lookup = pop2.groupby("cod_municipio")

    def choose_pop(row):
        if pd.notna(row.get("populacao_exata")) and row.get("populacao_exata", 0) > 0:
            return row["populacao_exata"], int(row["ano"]), row.get("fonte_populacao_exata", "População exata"), "exata"
        sub = pop_lookup.get_group(row["cod_municipio"]) if row["cod_municipio"] in pop_lookup.groups else pd.DataFrame()
        if not sub.empty:
            sub = sub.assign(diff=(sub["ano"].astype(int) - int(row["ano"])).abs()).sort_values(["diff", "ano"])
            best = sub.iloc[0]
            return best["populacao"], int(best["ano"]), best.get("fonte_populacao", "População aproximada"), "ano_mais_proximo"
        return row.get("populacao_ibge_2022", 0), 2022, "IBGE 2022 da tabela de regiões", "fallback_2022"

    chosen = panel.apply(lambda r: choose_pop(r), axis=1, result_type="expand")
    chosen.columns = ["populacao_usada", "ano_populacao_usado", "fonte_populacao", "tipo_populacao"]
    panel = pd.concat([panel, chosen], axis=1)
    panel["populacao_usada"] = pd.to_numeric(panel["populacao_usada"], errors="coerce").fillna(0)
    panel["taxa_municipal"] = panel.apply(lambda r: r["vinculos"] / r["populacao_usada"] * tax_base if r["populacao_usada"] > 0 else 0, axis=1)
    return panel


# ============================================================
# VALIDAÇÃO INICIAL
# ============================================================

st.markdown('<div class="ow-title">OdontoWorkforce Brasil — V4</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ow-subtitle">Distribuição da força de trabalho odontológica, especialidades, taxas per capita e comparações regionais.</div>',
    unsafe_allow_html=True,
)

if not DB_PATH.exists():
    st.error(f"Banco DuckDB não encontrado: {DB_PATH}")
    st.stop()

cols = get_table_columns()
if not cols:
    st.error(f"Tabela `{TABLE}` não encontrada no banco {DB_PATH}.")
    st.stop()

ano_col = pick(cols, ["ano"])
municipio_col = pick(cols, ["municipio", "co_municipio", "cod_municipio", "Município"])
cbo_col = pick(cols, ["cbo", "cbo_ocupacao_2002", "CBO Ocupação 2002"])
cbo_desc_col = pick(cols, ["cbo_nome", "cbo_descricao", "descricao_cbo", "ocupacao", "ocupacao_nome"])
uf_col_db = pick(cols, ["uf_nome", "uf", "uf_sigla", "sg_uf"])
sexo_col = pick(cols, ["sexo", "sexo_trabalhador", "Sexo Trabalhador"])
raca_col = pick(cols, ["raca_cor", "raça_cor", "raca", "Raça Cor"])
idade_col = pick(cols, ["idade", "Idade"])
setor_col = pick(cols, ["natureza_juridica", "tipo_vinculo", "cnae_divisao", "cnae", "CNAE 2.0 Classe"])
horas_col = pick(cols, ["horas_semanais", "qtd_hora_contr", "Qtd Hora Contr"])
salario_cols = [c for c in ["remuneracao_media_mensal", "remuneracao_hora", "remun_media", "vl_remun_media_nom", "Vl Remun Média Nom"] if c in cols]

if not all([ano_col, municipio_col, cbo_col]):
    st.error(f"Colunas essenciais não detectadas. ano={ano_col}, municipio={municipio_col}, cbo={cbo_col}")
    st.stop()

territory, territory_path = load_territory()
pop_mun, population_path = load_population_municipal(territory)

# ============================================================
# FILTROS
# ============================================================

st.sidebar.title("Filtros")

years = get_years(ano_col)
ano_ini, ano_fim = st.sidebar.slider(
    "Período",
    min_value=min(years),
    max_value=max(years),
    value=(min(years), max(years)),
    step=1,
)
selected_years = list(range(ano_ini, ano_fim + 1))
base_where = [f"CAST({q(ano_col)} AS INTEGER) BETWEEN {ano_ini} AND {ano_fim}"]

# Território
territory_filtered = territory.copy() if territory is not None else None
if territory_filtered is not None:
    st.sidebar.markdown("### Território")
    uf_options = territory_filtered["sg_uf"].dropna().sort_values().unique().tolist()
    selected_ufs = st.sidebar.multiselect("UF", uf_options, default=uf_options)
    if selected_ufs:
        territory_filtered = territory_filtered[territory_filtered["sg_uf"].isin(selected_ufs)].copy()

    macro_options = territory_filtered["macrorregiao_de_saude"].dropna().sort_values().unique().tolist()
    selected_macros = st.sidebar.multiselect("Macrorregião de saúde", macro_options, default=macro_options)
    if selected_macros:
        territory_filtered = territory_filtered[territory_filtered["macrorregiao_de_saude"].isin(selected_macros)].copy()

    reg_options = territory_filtered["regiao_de_saude"].dropna().sort_values().unique().tolist()
    selected_regs = st.sidebar.multiselect("Região de saúde", reg_options, default=reg_options)
    if selected_regs:
        territory_filtered = territory_filtered[territory_filtered["regiao_de_saude"].isin(selected_regs)].copy()

    with st.sidebar.expander("Municípios", expanded=False):
        termo_mun = st.text_input("Buscar município", "")
        mun_df = territory_filtered.copy()
        if termo_mun.strip():
            termo = termo_mun.strip().lower()
            mun_df = mun_df[mun_df["municipio_label"].str.lower().str.contains(termo, na=False)]
        mun_options = mun_df.sort_values("municipio_label")["municipio_label"].tolist()
        mun_map = dict(zip(mun_df["municipio_label"], mun_df["cod_municipio"]))
        selected_mun_labels = st.multiselect("Selecionar municípios", mun_options, default=[])
        if selected_mun_labels:
            territory_filtered = territory_filtered[territory_filtered["cod_municipio"].isin([mun_map[x] for x in selected_mun_labels])].copy()

    mun_codes = territory_filtered["cod_municipio"].dropna().astype(str).unique().tolist()
    all_mun_codes = territory["cod_municipio"].dropna().astype(str).unique().tolist()
    if len(mun_codes) < len(all_mun_codes):
        base_where.append(f"{mun_key_expr(municipio_col)} IN ({','.join(lit(x) for x in mun_codes)})")

# CBO / especialidades
st.sidebar.markdown("### Especialidades odontológicas")
cbo_options_df = get_cbo_options(cbo_col, cbo_desc_col)

group_options = cbo_options_df["grupo_cbo"].dropna().sort_values().unique().tolist()
selected_groups = st.sidebar.multiselect("Grupo ocupacional", group_options, default=group_options)

family_options = cbo_options_df[cbo_options_df["grupo_cbo"].isin(selected_groups)]["familia_cbo"].dropna().sort_values().unique().tolist()
selected_families = st.sidebar.multiselect("Família de especialidade", family_options, default=family_options)

search_cbo = st.sidebar.text_input("Buscar especialidade/CBO", "")
filtered_cbo = cbo_options_df[
    cbo_options_df["grupo_cbo"].isin(selected_groups) & cbo_options_df["familia_cbo"].isin(selected_families)
].copy()
if search_cbo.strip():
    s = search_cbo.strip().lower()
    filtered_cbo = filtered_cbo[
        filtered_cbo["label"].str.lower().str.contains(s, na=False)
        | filtered_cbo["cbo"].str.lower().str.contains(s, na=False)
    ]

cbo_mode = st.sidebar.radio("Modo de seleção", ["Todas filtradas", "Top N", "Escolha manual"], index=0)
top_n = st.sidebar.slider("Top N especialidades nos gráficos", 5, 50, 20, 5)

if cbo_mode == "Top N":
    selected_cbos = filtered_cbo.head(top_n)["cbo"].tolist()
    st.sidebar.caption(f"Selecionadas automaticamente as {len(selected_cbos)} especialidades mais frequentes.")
elif cbo_mode == "Escolha manual":
    cbo_label_map = dict(zip(filtered_cbo["label"], filtered_cbo["cbo"]))
    selected_cbo_labels = st.sidebar.multiselect("Especialidade / CBO", filtered_cbo["label"].tolist(), default=filtered_cbo.head(min(12, len(filtered_cbo)))["label"].tolist())
    selected_cbos = [cbo_label_map[x] for x in selected_cbo_labels]
else:
    selected_cbos = filtered_cbo["cbo"].tolist()

all_cbos = cbo_options_df["cbo"].tolist()
if selected_cbos and len(selected_cbos) < len(all_cbos):
    base_where.append(f"{cbo_key_expr(cbo_col)} IN ({','.join(lit(x) for x in selected_cbos)})")

# Filtros complementares
st.sidebar.markdown("### Outros filtros")

def add_dim_filter(col: str | None, title: str, mapping: dict[str, str] | None = None):
    if not col:
        return
    vals = sql_df(f"""
        SELECT CAST({q(col)} AS VARCHAR) AS valor, COUNT(*) AS n
        FROM {TABLE}
        WHERE {q(col)} IS NOT NULL
        GROUP BY 1
        ORDER BY n DESC
        LIMIT 120
    """)
    if vals.empty:
        return
    if mapping:
        vals["rotulo"] = vals["valor"].map(lambda x: value_label(x, mapping))
    else:
        vals["rotulo"] = vals["valor"].astype(str)
    vals["label"] = vals["rotulo"].astype(str) + " (" + vals["n"].map(fmt_int) + ")"
    label_map = dict(zip(vals["label"], vals["valor"]))
    selected = st.sidebar.multiselect(title, vals["label"].tolist(), default=vals["label"].tolist())
    if selected and len(selected) < len(vals):
        base_where.append(f"CAST({q(col)} AS VARCHAR) IN ({','.join(lit(label_map[x]) for x in selected)})")

add_dim_filter(sexo_col, "Sexo", SEX_LABELS)
add_dim_filter(raca_col, "Raça/cor", RACE_LABELS)
add_dim_filter(setor_col, "Setor / natureza do vínculo", None)

tax_base = st.sidebar.selectbox("Base da taxa", [10_000, 100_000], index=0)
tax_label = f"vínculos por {tax_base:,} hab.".replace(",", ".")
where_sql = " AND ".join(base_where)

st.sidebar.markdown("---")
st.sidebar.caption("Arquivos e dicionários")
st.sidebar.write(f"Banco: `{DB_PATH.name}`")
if territory_path:
    st.sidebar.write(f"Regiões: `{Path(territory_path).name}`")
if population_path:
    st.sidebar.write(f"População: `{Path(population_path).name}`")
st.sidebar.write(f"CBOs filtrados: **{len(selected_cbos)}**")

# ============================================================
# CONSULTAS BASE
# ============================================================

@st.cache_data(show_spinner=True)
def get_series_counts(where_sql_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios_com_vinculo,
            COUNT(DISTINCT {cbo_key_expr(cbo_col)}) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1
        ORDER BY 1
    """)


@st.cache_data(show_spinner=True)
def get_municipal_counts(where_sql_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            {mun_key_expr(municipio_col)} AS cod_municipio,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {cbo_key_expr(cbo_col)}) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)


series_df = get_series_counts(where_sql)
municipal_panel = pd.DataFrame()
if territory_filtered is not None:
    municipal_counts = get_municipal_counts(where_sql)
    municipal_panel = complete_municipal_panel(municipal_counts, territory_filtered, pop_mun, selected_years, tax_base)

# ============================================================
# KPIs
# ============================================================

if not series_df.empty:
    total_vinc = int(series_df["vinculos"].sum())
    mun_com_vinc = int(series_df["municipios_com_vinculo"].max())
    cbos = int(series_df["ocupacoes_cbo"].max())
else:
    total_vinc = mun_com_vinc = cbos = 0

if not municipal_panel.empty:
    pop_media_periodo = municipal_panel.groupby("ano")["populacao_usada"].sum().mean()
    taxa_media = total_vinc / (pop_media_periodo * len(selected_years)) * tax_base if pop_media_periodo and selected_years else 0
    mun_total = municipal_panel["cod_municipio"].nunique()
else:
    taxa_media = 0
    mun_total = None

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Vínculos", fmt_int(total_vinc))
c2.metric("Municípios com vínculo", fmt_int(mun_com_vinc))
c3.metric("CBOs / ocupações", fmt_int(cbos))
if mun_total is not None:
    c4.metric("Municípios no filtro", fmt_int(mun_total))
else:
    c4.metric("Período", f"{ano_ini}–{ano_fim}")
c5.metric(f"Taxa média — {tax_label}", fmt_float(taxa_media, 2) if mun_total else "—")

# ============================================================
# ABAS
# ============================================================

tabs = st.tabs([
    "Visão geral",
    "Taxas per capita",
    "Regiões e macrorregiões",
    "Especialidades odontológicas",
    "Perfil e desigualdades",
    "Panorama salarial",
    "Setor / vínculo",
    "Diagnóstico e exportações",
])

with tabs[0]:
    st.subheader("Visão geral")
    st.markdown('<div class="ow-note">Esta versão usa rótulos legíveis para CBOs e dimensões principais. Os filtros da barra lateral são aplicados simultaneamente.</div>', unsafe_allow_html=True)
    show_table(series_df)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if not series_df.empty:
            fig = px.line(series_df, x="ano", y="vinculos", markers=True, title="Evolução dos vínculos odontológicos", labels=COLUMN_LABELS)
            fig.update_xaxes(dtick=1)
            plot(fig)
    with c2:
        if not series_df.empty:
            fig = px.bar(series_df, x="ano", y="municipios_com_vinculo", text="municipios_com_vinculo", title="Municípios com vínculo", labels=COLUMN_LABELS)
            fig.update_xaxes(dtick=1)
            plot(fig)
    download_buttons(series_df, "visao_geral")

with tabs[1]:
    st.subheader("Taxas per capita e variação municipal")
    if municipal_panel.empty:
        st.warning("A visão per capita exige tabela de regiões e população municipal.")
    else:
        taxa_col = "taxa_municipal"
        c1, c2 = st.columns([1.2, 1])
        with c1:
            fig = px.box(municipal_panel, x="ano", y=taxa_col, points="outliers", title=f"Distribuição municipal da taxa — {tax_label}", labels={**COLUMN_LABELS, taxa_col: tax_label})
            fig.update_xaxes(type="category")
            plot(fig)
        with c2:
            resumo = municipal_panel.groupby("ano", as_index=False).agg(
                vinculos=("vinculos", "sum"),
                populacao_usada=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                media_taxa=(taxa_col, "mean"),
                mediana_taxa=(taxa_col, "median"),
                p25=(taxa_col, lambda x: x.quantile(.25)),
                p75=(taxa_col, lambda x: x.quantile(.75)),
            )
            resumo["taxa_agregada"] = resumo["vinculos"] / resumo["populacao_usada"] * tax_base
            show_table(resumo)
            download_buttons(resumo, "resumo_taxas_ano")
        st.markdown("### Variação por UF")
        fig = px.box(municipal_panel, x="sg_uf", y=taxa_col, color="ano", points=False, title=f"Boxplot municipal por UF — {tax_label}", labels={taxa_col: tax_label, "sg_uf": "UF"})
        plot(fig)
        ultimo = max(selected_years)
        last = municipal_panel[municipal_panel["ano"] == ultimo].copy()
        top = last.sort_values(taxa_col, ascending=False).head(30)
        st.markdown(f"### Municípios com maiores taxas — {ultimo}")
        show_table(top[["ano", "municipio_label", "regiao_de_saude", "macrorregiao_de_saude", "vinculos", "populacao_usada", "taxa_municipal"]])
        fig = px.bar(top.sort_values(taxa_col), x=taxa_col, y="municipio_label", orientation="h", title=f"Top 30 municípios — {tax_label}", labels={taxa_col: tax_label, "municipio_label": "Município"})
        plot(fig)
        download_buttons(municipal_panel, "painel_municipal_taxas")

with tabs[2]:
    st.subheader("Comparações regionais")
    if municipal_panel.empty:
        st.warning("A comparação regional exige tabela de regiões.")
    else:
        reg = municipal_panel.groupby(["ano", "sg_uf", "cod_regiao_de_saude", "regiao_de_saude"], as_index=False).agg(
            vinculos=("vinculos", "sum"), populacao_usada=("populacao_usada", "sum"), municipios=("cod_municipio", "nunique"), mediana_municipal=("taxa_municipal", "median")
        )
        reg["taxa_regional"] = reg["vinculos"] / reg["populacao_usada"] * tax_base
        macro = municipal_panel.groupby(["ano", "sg_uf", "cod_macrorregiao_de_saude", "macrorregiao_de_saude"], as_index=False).agg(
            vinculos=("vinculos", "sum"), populacao_usada=("populacao_usada", "sum"), municipios=("cod_municipio", "nunique"), mediana_municipal=("taxa_municipal", "median")
        )
        macro["taxa_macro"] = macro["vinculos"] / macro["populacao_usada"] * tax_base
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Regiões de saúde")
            show_table(reg)
            fig = px.box(reg, x="ano", y="taxa_regional", points="all", title=f"Taxas entre regiões de saúde — {tax_label}", labels={"taxa_regional": tax_label})
            fig.update_xaxes(type="category")
            plot(fig)
        with c2:
            st.markdown("### Macrorregiões de saúde")
            show_table(macro)
            fig = px.box(macro, x="ano", y="taxa_macro", points="all", title=f"Taxas entre macrorregiões — {tax_label}", labels={"taxa_macro": tax_label})
            fig.update_xaxes(type="category")
            plot(fig)
        last_macro = macro[macro["ano"] == max(selected_years)].sort_values("taxa_macro", ascending=False).head(30)
        fig = px.bar(last_macro.sort_values("taxa_macro"), x="taxa_macro", y="macrorregiao_de_saude", color="sg_uf", orientation="h", title=f"Top 30 macrorregiões — {max(selected_years)}", labels={"taxa_macro": tax_label})
        plot(fig)
        download_buttons(reg, "regioes_macrorregioes", {"regioes": reg, "macrorregioes": macro})

with tabs[3]:
    st.subheader("Especialidades odontológicas")
    cbo_summary = sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            {cbo_key_expr(cbo_col)} AS cbo,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
        FROM {TABLE}
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """)
    if not cbo_summary.empty:
        cbo_summary = cbo_summary.merge(cbo_options_df[["cbo", "cbo_nome", "grupo_cbo", "familia_cbo"]], on="cbo", how="left")
        cbo_summary["cbo_nome"] = cbo_summary["cbo_nome"].fillna(cbo_summary["cbo"].map(cbo_fallback_name))
        cbo_summary["cbo_label"] = cbo_summary["cbo_nome"] + " — " + cbo_summary["cbo"]
        show_table(cbo_summary)
        top_cbo = cbo_summary.groupby("cbo_label")["vinculos"].sum().sort_values(ascending=False).head(top_n).index
        top_df = cbo_summary[cbo_summary["cbo_label"].isin(top_cbo)].copy()
        c1, c2 = st.columns([1.1, 1])
        with c1:
            fig = px.bar(top_df, x="cbo_label", y="vinculos", color="ano", barmode="group", title=f"Top {top_n} especialidades/CBO", labels=COLUMN_LABELS)
            plot(fig)
        with c2:
            fig = px.line(top_df, x="ano", y="vinculos", color="cbo_label", markers=True, title="Evolução das principais especialidades", labels=COLUMN_LABELS)
            fig.update_xaxes(dtick=1)
            plot(fig)
        heat = top_df.copy()
        fig = px.density_heatmap(heat, x="ano", y="cbo_label", z="vinculos", histfunc="sum", title="Mapa de calor — vínculos por especialidade e ano", labels=COLUMN_LABELS)
        fig.update_xaxes(dtick=1)
        plot(fig)
        if not municipal_panel.empty:
            cbos_box = cbo_summary.groupby("cbo")['vinculos'].sum().sort_values(ascending=False).head(min(8, top_n)).index.tolist()
            cbo_mun = sql_df(f"""
                SELECT
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    {mun_key_expr(municipio_col)} AS cod_municipio,
                    {cbo_key_expr(cbo_col)} AS cbo,
                    COUNT(*) AS vinculos
                FROM {TABLE}
                WHERE {where_sql}
                  AND {cbo_key_expr(cbo_col)} IN ({','.join(lit(x) for x in cbos_box)})
                GROUP BY 1, 2, 3
            """)
            if not cbo_mun.empty and territory_filtered is not None:
                base_grid = pd.MultiIndex.from_product([selected_years, territory_filtered['cod_municipio'].tolist(), cbos_box], names=['ano', 'cod_municipio', 'cbo']).to_frame(index=False)
                pop_base = municipal_panel[['ano','cod_municipio','municipio_label','sg_uf','regiao_de_saude','macrorregiao_de_saude','populacao_usada']].drop_duplicates(['ano','cod_municipio'])
                cbo_panel = base_grid.merge(pop_base, on=['ano','cod_municipio'], how='left').merge(cbo_mun, on=['ano','cod_municipio','cbo'], how='left')
                cbo_panel['vinculos'] = cbo_panel['vinculos'].fillna(0)
                cbo_panel['taxa_municipal'] = cbo_panel.apply(lambda r: r['vinculos'] / r['populacao_usada'] * tax_base if r['populacao_usada'] and r['populacao_usada'] > 0 else 0, axis=1)
                cbo_panel = cbo_panel.merge(cbo_options_df[['cbo','cbo_nome','grupo_cbo','familia_cbo']], on='cbo', how='left')
                cbo_panel['cbo_label'] = cbo_panel['cbo_nome'].fillna(cbo_panel['cbo'].map(cbo_fallback_name)) + ' — ' + cbo_panel['cbo']
                fig = px.box(cbo_panel, x='cbo_label', y='taxa_municipal', color='ano', points=False, title=f'Variação municipal das taxas por especialidade — {tax_label}', labels={'taxa_municipal': tax_label, 'cbo_label': 'Especialidade / CBO'})
                plot(fig)
        download_buttons(cbo_summary, "especialidades_odontologicas")
    else:
        st.warning("Nenhuma especialidade/CBO encontrada para os filtros selecionados.")

with tabs[4]:
    st.subheader("Perfil e desigualdades")
    dims = []
    if sexo_col:
        dims.append(("Sexo", sexo_col, SEX_LABELS))
    if raca_col:
        dims.append(("Raça/cor", raca_col, RACE_LABELS))
    if uf_col_db:
        dims.append(("UF no banco", uf_col_db, None))
    if not dims:
        st.warning("Colunas de perfil não detectadas.")
    else:
        export = {}
        for title, col, mapping in dims:
            df = sql_df(f"""
                SELECT CAST({q(ano_col)} AS INTEGER) AS ano, CAST({q(col)} AS VARCHAR) AS valor, COUNT(*) AS vinculos
                FROM {TABLE}
                WHERE {where_sql} AND {q(col)} IS NOT NULL
                GROUP BY 1, 2
                ORDER BY 1, 3 DESC
            """)
            if mapping:
                df["grupo"] = df["valor"].map(lambda x: value_label(x, mapping))
            else:
                df["grupo"] = df["valor"].astype(str)
            export[title] = df
            st.markdown(f"### {title}")
            show_table(df[["ano", "grupo", "vinculos"]])
            fig = px.bar(df, x="grupo", y="vinculos", color="ano", barmode="group", title=f"Vínculos por {title}", labels={"grupo": title, "vinculos": "Vínculos"})
            plot(fig)
        first = next(iter(export.values()))
        download_buttons(first, "perfil_desigualdades", export)

with tabs[5]:
    st.subheader("Panorama salarial")
    if not salario_cols:
        st.warning("Nenhuma coluna salarial detectada.")
    else:
        diagnostics = []
        for col in salario_cols:
            expr = numeric_expr(col)
            d = sql_df(f"""
                SELECT '{col}' AS coluna, CAST({q(ano_col)} AS INTEGER) AS ano, COUNT(*) AS registros,
                       SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS validos,
                       AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS media
                FROM {TABLE}
                WHERE {where_sql}
                GROUP BY 1,2
                ORDER BY 2
            """)
            diagnostics.append(d)
        diag = pd.concat(diagnostics, ignore_index=True)
        best_col = diag.groupby("coluna")["validos"].sum().sort_values(ascending=False).index[0]
        expr = numeric_expr(best_col)
        st.markdown(f'<div class="ow-note">Coluna salarial usada nos gráficos: <b>{best_col}</b>.</div>', unsafe_allow_html=True)
        sal = sql_df(f"""
            SELECT CAST({q(ano_col)} AS INTEGER) AS ano,
                   SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS registros_validos,
                   AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_media,
                   MEDIAN(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_mediana,
                   QUANTILE_CONT(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END, .25) AS p25,
                   QUANTILE_CONT(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END, .75) AS p75
            FROM {TABLE}
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY 1
        """)
        show_table(sal)
        if not sal.dropna(subset=["remuneracao_media"]).empty:
            fig = px.line(sal, x="ano", y=["remuneracao_media", "remuneracao_mediana", "p25", "p75"], markers=True, title="Remuneração — média, mediana e quartis", labels=COLUMN_LABELS)
            fig.update_xaxes(dtick=1)
            plot(fig)
        download_buttons(sal, "panorama_salarial", {"salarios": sal, "diagnostico_salarios": diag})

with tabs[6]:
    st.subheader("Setor / tipo de vínculo")
    if not setor_col:
        st.warning("Coluna de setor ou tipo de vínculo não detectada.")
    else:
        setor = sql_df(f"""
            SELECT CAST({q(ano_col)} AS INTEGER) AS ano, CAST({q(setor_col)} AS VARCHAR) AS setor,
                   COUNT(*) AS vinculos, COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios,
                   COUNT(DISTINCT {cbo_key_expr(cbo_col)}) AS ocupacoes_cbo
            FROM {TABLE}
            WHERE {where_sql} AND {q(setor_col)} IS NOT NULL
            GROUP BY 1,2
            ORDER BY 1,3 DESC
        """)
        show_table(setor)
        if not setor.empty:
            top = setor.groupby("setor")["vinculos"].sum().sort_values(ascending=False).head(20).index
            fig = px.bar(setor[setor["setor"].isin(top)], x="setor", y="vinculos", color="ano", barmode="group", title="Top 20 setores/tipos de vínculo", labels=COLUMN_LABELS)
            plot(fig)
        download_buttons(setor, "setor_tipo_vinculo")

with tabs[7]:
    st.subheader("Diagnóstico e exportações")
    st.markdown('<div class="ow-note">As tabelas exportadas usam nomes legíveis nas colunas. A aba também mostra a cobertura dos denominadores populacionais.</div>', unsafe_allow_html=True)
    show_table(series_df)
    exports = {"serie_temporal": series_df, "cbo_mapa": cbo_options_df, "colunas_banco": pd.DataFrame({"coluna_original": cols, "nome_legivel": [COLUMN_LABELS.get(c, c.replace("_", " ").title()) for c in cols]})}
    if not municipal_panel.empty:
        pop_status = municipal_panel.groupby(["ano", "tipo_populacao", "ano_populacao_usado"], as_index=False).agg(municipios=("cod_municipio", "nunique"), populacao_usada=("populacao_usada", "sum"))
        st.markdown("### Cobertura dos denominadores populacionais")
        show_table(pop_status)
        exports["municipios_taxas"] = municipal_panel
        exports["cobertura_populacao"] = pop_status
    show_table(exports["colunas_banco"])
    download_buttons(series_df, "exportacao_geral_v4", exports)
