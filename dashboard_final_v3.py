
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURAÇÃO GERAL
# ============================================================

DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
TABLE = "odontologia_vinculos"

APP_DIR = Path(__file__).resolve().parent
TERRITORY_CANDIDATES = [
    APP_DIR / "reference" / "tabela_regioes(1).csv",
    APP_DIR / "reference" / "tabela_regioes.csv",
    APP_DIR / "tabela_regioes(1).csv",
    APP_DIR / "tabela_regioes.csv",
]

POPULATION_CANDIDATES = [
    APP_DIR / "reference" / "populacao_tcu_municipios.csv",
    APP_DIR / "populacao_tcu_municipios.csv",
]

POPULATION_UF_CANDIDATES = [
    APP_DIR / "reference" / "populacao_tcu_uf.csv",
    APP_DIR / "populacao_tcu_uf.csv",
]

st.set_page_config(
    page_title="OdontoWorkforce Brasil — Painel Avançado V3",
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
        padding-top: 1.0rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }
    .ow-title {
        font-size: 2.35rem;
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: -0.04em;
        margin-bottom: 0.15rem;
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
    .ow-small {
        color: #64748b;
        font-size: 0.92rem;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #e6edf5;
        padding: 1rem;
        border-radius: 1.05rem;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.055);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.65rem;
        font-weight: 800;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: .35rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        padding: .45rem .8rem;
        background-color: #f8fafc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
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


def connect(read_only: bool = True):
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def sql_df(sql: str) -> pd.DataFrame:
    con = connect(read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def plot(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def show_table(df: pd.DataFrame, height: int | str | None = None):
    kwargs = {"hide_index": True}

    if height is not None:
        kwargs["height"] = height

    try:
        st.dataframe(df, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kwargs)


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = name[:31].replace("/", "_").replace("\\", "_")
            df.to_excel(writer, index=False, sheet_name=safe)
    return output.getvalue()


def download_buttons(df: pd.DataFrame, base_name: str, sheets: dict[str, pd.DataFrame] | None = None):
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{base_name}.csv",
            mime="text/csv",
            key=f"{base_name}_csv",
            width="stretch",
        )
    with c2:
        st.download_button(
            "⬇️ Excel",
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


def mun_key_expr(col: str) -> str:
    # A RAIS usualmente traz Município como código IBGE de 6 dígitos.
    # Esta expressão normaliza inteiro/texto e preserva zeros à esquerda.
    return f"""
    RIGHT(
        '000000' || REGEXP_REPLACE(CAST({q(col)} AS VARCHAR), '[^0-9]', '', 'g'),
        6
    )
    """


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
def get_cbo_options(cbo_col: str, cbo_desc_col: str | None = None) -> pd.DataFrame:
    if cbo_desc_col:
        sql = f"""
            SELECT
                CAST({q(cbo_col)} AS VARCHAR) AS cbo,
                ANY_VALUE(CAST({q(cbo_desc_col)} AS VARCHAR)) AS cbo_nome,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE {q(cbo_col)} IS NOT NULL
            GROUP BY 1
            ORDER BY vinculos DESC
        """
    else:
        sql = f"""
            SELECT
                CAST({q(cbo_col)} AS VARCHAR) AS cbo,
                CAST({q(cbo_col)} AS VARCHAR) AS cbo_nome,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE {q(cbo_col)} IS NOT NULL
            GROUP BY 1
            ORDER BY vinculos DESC
        """
    df = sql_df(sql)
    df["label"] = df["cbo"].astype(str) + " — " + df["cbo_nome"].astype(str) + " (" + df["vinculos"].map(fmt_int) + ")"
    return df


def find_territory_file() -> Path | None:
    for p in TERRITORY_CANDIDATES:
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_territory_from_path(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    df = pd.read_csv(path, sep=";", dtype={"cod_municipio": str})
    df.columns = [c.strip() for c in df.columns]

    required = [
        "sg_uf",
        "uf",
        "cod_municipio",
        "no_municipio",
        "regiao_de_saude",
        "macrorregiao_de_saude",
        "populacao_ibge_2022",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na tabela de regiões: {missing}")

    df["cod_municipio"] = (
        df["cod_municipio"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str[-6:]
        .str.zfill(6)
    )
    df["populacao_ibge_2022"] = pd.to_numeric(df["populacao_ibge_2022"], errors="coerce").fillna(0)
    df["municipio_nome_limpo"] = (
        df["no_municipio"]
        .astype(str)
        .str.replace(r"^[A-Z]{2}\s*-\s*", "", regex=True)
        .str.title()
    )
    df["municipio_label"] = df["sg_uf"].astype(str) + " — " + df["municipio_nome_limpo"].astype(str)

    # Garantia de unicidade municipal.
    df = df.drop_duplicates(subset=["cod_municipio"]).copy()
    return df


def load_territory() -> tuple[pd.DataFrame | None, str]:
    found = find_territory_file()
    if found:
        return load_territory_from_path(str(found)), str(found)

    uploaded = st.sidebar.file_uploader("Carregar tabela_regioes CSV", type=["csv"])
    if uploaded is None:
        return None, ""

    df = pd.read_csv(uploaded, sep=";", dtype={"cod_municipio": str})
    tmp = APP_DIR / "reference" / "tabela_regioes_uploaded.csv"
    tmp.parent.mkdir(exist_ok=True)
    df.to_csv(tmp, sep=";", index=False, encoding="utf-8")
    return load_territory_from_path(str(tmp)), str(tmp)



def find_population_file() -> Path | None:
    for p in POPULATION_CANDIDATES:
        if p.exists():
            return p
    return None


def find_population_uf_file() -> Path | None:
    for p in POPULATION_UF_CANDIDATES:
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_population_municipal_from_path(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    df = pd.read_csv(path, sep=";", dtype={"cod_municipio": str, "cod_municipio7": str})
    df.columns = [c.strip() for c in df.columns]

    required = ["ano", "cod_municipio", "populacao"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no arquivo de populações municipais: {missing}")

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["cod_municipio"] = (
        df["cod_municipio"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str[-6:]
        .str.zfill(6)
    )
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    if "fonte_populacao" not in df.columns:
        df["fonte_populacao"] = path.name

    df = df.dropna(subset=["ano", "cod_municipio", "populacao"]).copy()
    df["ano"] = df["ano"].astype(int)
    df = df.drop_duplicates(subset=["ano", "cod_municipio"]).copy()
    return df


def load_population_municipal() -> tuple[pd.DataFrame | None, str]:
    found = find_population_file()
    if found:
        return load_population_municipal_from_path(str(found)), str(found)
    return None, ""


@st.cache_data(show_spinner=False)
def load_population_uf_from_path(path_str: str) -> pd.DataFrame:
    path = Path(path_str)
    df = pd.read_csv(path, sep=";", dtype={"sg_uf": str})
    df.columns = [c.strip() for c in df.columns]
    if not {"ano", "sg_uf", "populacao"}.issubset(set(df.columns)):
        return pd.DataFrame()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    df = df.dropna(subset=["ano", "sg_uf", "populacao"]).copy()
    df["ano"] = df["ano"].astype(int)
    return df


def load_population_uf() -> tuple[pd.DataFrame | None, str]:
    found = find_population_uf_file()
    if found:
        return load_population_uf_from_path(str(found)), str(found)
    return None, ""


def build_population_grid(
    territory_base: pd.DataFrame,
    years_selected: list[int],
    pop_mun: pd.DataFrame | None,
) -> pd.DataFrame:
    grid = pd.MultiIndex.from_product(
        [years_selected, territory_base["cod_municipio"].tolist()],
        names=["ano", "cod_municipio"],
    ).to_frame(index=False)

    if pop_mun is None or pop_mun.empty:
        fallback = territory_base[["cod_municipio", "populacao_ibge_2022"]].copy()
        fallback["populacao_usada"] = pd.to_numeric(fallback["populacao_ibge_2022"], errors="coerce").fillna(0)
        fallback["ano_populacao"] = 2022
        fallback["fonte_populacao_usada"] = "tabela_regioes populacao_ibge_2022"
        fallback["tipo_populacao"] = "fallback_2022"
        fallback = fallback[["cod_municipio", "populacao_usada", "ano_populacao", "fonte_populacao_usada", "tipo_populacao"]]
        return grid.merge(fallback, on="cod_municipio", how="left")

    pop = pop_mun[["ano", "cod_municipio", "populacao", "fonte_populacao"]].copy()
    pop["cod_municipio"] = pop["cod_municipio"].astype(str).str[-6:].str.zfill(6)
    pop["populacao"] = pd.to_numeric(pop["populacao"], errors="coerce")

    exact = pop.rename(
        columns={
            "populacao": "populacao_usada",
            "ano": "ano_populacao",
            "fonte_populacao": "fonte_populacao_usada",
        }
    )

    merged = grid.merge(
        exact,
        left_on=["ano", "cod_municipio"],
        right_on=["ano_populacao", "cod_municipio"],
        how="left",
    )
    merged["tipo_populacao"] = merged["ano_populacao"].where(merged["ano_populacao"].isna(), "exata")
    merged.loc[merged["ano_populacao"].notna(), "tipo_populacao"] = "exata"

    # Para anos sem população municipal exata, usar o ano disponível mais próximo por município.
    missing = merged["populacao_usada"].isna()
    if missing.any():
        nearest_frames = []
        for year in sorted(merged.loc[missing, "ano"].unique()):
            p = pop.copy()
            p["dist"] = (p["ano"] - int(year)).abs()
            p = (
                p.sort_values(["cod_municipio", "dist", "ano"])
                .drop_duplicates("cod_municipio")
                .rename(
                    columns={
                        "ano": "ano_populacao",
                        "populacao": "populacao_usada",
                        "fonte_populacao": "fonte_populacao_usada",
                    }
                )
            )
            p["ano"] = int(year)
            p["tipo_populacao"] = "fallback_ano_mais_proximo"
            nearest_frames.append(p[["ano", "cod_municipio", "populacao_usada", "ano_populacao", "fonte_populacao_usada", "tipo_populacao"]])

        nearest = pd.concat(nearest_frames, ignore_index=True) if nearest_frames else pd.DataFrame()
        fill = merged.loc[missing, ["ano", "cod_municipio"]].merge(
            nearest, on=["ano", "cod_municipio"], how="left"
        )
        for col in ["populacao_usada", "ano_populacao", "fonte_populacao_usada", "tipo_populacao"]:
            merged.loc[missing, col] = fill[col].values

    # Fallback final para população 2022 da tabela de regiões.
    missing = merged["populacao_usada"].isna()
    if missing.any() and "populacao_ibge_2022" in territory_base.columns:
        terr_pop = territory_base[["cod_municipio", "populacao_ibge_2022"]].copy()
        terr_pop["populacao_ibge_2022"] = pd.to_numeric(terr_pop["populacao_ibge_2022"], errors="coerce")
        fill = merged.loc[missing, ["cod_municipio"]].merge(terr_pop, on="cod_municipio", how="left")
        merged.loc[missing, "populacao_usada"] = fill["populacao_ibge_2022"].values
        merged.loc[missing, "ano_populacao"] = 2022
        merged.loc[missing, "fonte_populacao_usada"] = "tabela_regioes populacao_ibge_2022"
        merged.loc[missing, "tipo_populacao"] = "fallback_2022"

    merged["populacao_usada"] = pd.to_numeric(merged["populacao_usada"], errors="coerce").fillna(0)
    merged["ano_populacao"] = pd.to_numeric(merged["ano_populacao"], errors="coerce").fillna(0).astype(int)
    return merged


# ============================================================
# VALIDAÇÃO INICIAL
# ============================================================

st.markdown('<div class="ow-title">OdontoWorkforce Brasil — Painel Avançado V3</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="ow-subtitle">RAIS odontologia com populações IBGE/TCU por ano, regiões de saúde, taxas per capita e exportações.</div>',
    unsafe_allow_html=True,
)

if not DB_PATH.exists():
    st.error(f"Banco DuckDB não encontrado: {DB_PATH}")
    st.stop()

cols = get_table_columns()
if not cols:
    st.error(f"Tabela `{TABLE}` não encontrada ou sem colunas no banco {DB_PATH}.")
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
    st.error(
        f"Colunas essenciais não detectadas. ano={ano_col}, municipio={municipio_col}, cbo={cbo_col}"
    )
    st.stop()

territory, territory_path = load_territory()
pop_mun, population_path = load_population_municipal()
pop_uf, population_uf_path = load_population_uf()

if territory is None:
    st.warning(
        "A tabela de regiões não foi encontrada. Coloque `tabela_regioes(1).csv` na pasta `reference/` "
        "ou carregue o arquivo pela barra lateral. Sem ela, as visões per capita e regionais ficam limitadas."
    )


# ============================================================
# FILTROS
# ============================================================

st.sidebar.title("Filtros")

years = get_years(ano_col)
if not years:
    st.error("Nenhum ano encontrado na base.")
    st.stop()

ano_ini, ano_fim = st.sidebar.slider(
    "Período",
    min_value=min(years),
    max_value=max(years),
    value=(min(years), max(years)),
    step=1,
)

base_where = [f"CAST({q(ano_col)} AS INTEGER) BETWEEN {ano_ini} AND {ano_fim}"]

# Filtros territoriais
territory_filtered = territory.copy() if territory is not None else None

if territory_filtered is not None:
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

    mun_codes = territory_filtered["cod_municipio"].dropna().astype(str).unique().tolist()
    all_mun_codes = territory["cod_municipio"].dropna().astype(str).unique().tolist()

    if len(mun_codes) < len(all_mun_codes):
        # DuckDB lida bem com lista de alguns milhares de códigos nesse volume.
        base_where.append(f"{mun_key_expr(municipio_col)} IN ({','.join(lit(x) for x in mun_codes)})")

# Filtro CBO
cbo_options_df = get_cbo_options(cbo_col, cbo_desc_col)
cbo_label_map = dict(zip(cbo_options_df["label"], cbo_options_df["cbo"]))

selected_cbo_labels = st.sidebar.multiselect(
    "CBO / Ocupação",
    options=cbo_options_df["label"].tolist(),
    default=cbo_options_df["label"].tolist(),
)

selected_cbos = [cbo_label_map[x] for x in selected_cbo_labels]
all_cbos = cbo_options_df["cbo"].tolist()

if selected_cbos and len(selected_cbos) < len(all_cbos):
    base_where.append(f"CAST({q(cbo_col)} AS VARCHAR) IN ({','.join(lit(x) for x in selected_cbos)})")

tax_base = st.sidebar.selectbox("Base da taxa", [10_000, 100_000], index=0)
tax_label = f"vínculos por {tax_base:,} hab.".replace(",", ".")

where_sql = " AND ".join(base_where)

st.sidebar.markdown("---")
st.sidebar.caption("Status")
st.sidebar.write(f"Banco: `{DB_PATH.name}`")
if territory_path:
    st.sidebar.write(f"Regiões: `{Path(territory_path).name}`")
if population_path:
    st.sidebar.write(f"Pop. municipal: `{Path(population_path).name}`")
if population_uf_path:
    st.sidebar.write(f"Pop. UF: `{Path(population_uf_path).name}`")
st.sidebar.caption("Colunas detectadas")
st.sidebar.json(
    {
        "ano": ano_col,
        "municipio": municipio_col,
        "cbo": cbo_col,
        "cbo_descricao": cbo_desc_col,
        "uf_db": uf_col_db,
        "sexo": sexo_col,
        "raca_cor": raca_col,
        "setor": setor_col,
        "salario": salario_cols,
    },
    expanded=False,
)


# ============================================================
# CONSULTAS BASE
# ============================================================

@st.cache_data(show_spinner=True)
def get_municipal_counts(where_sql_: str, ano_col_: str, municipio_col_: str, cbo_col_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col_)} AS INTEGER) AS ano,
            {mun_key_expr(municipio_col_)} AS cod_municipio,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {q(cbo_col_)}) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)


@st.cache_data(show_spinner=True)
def get_series_counts(where_sql_: str, ano_col_: str, municipio_col_: str, cbo_col_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col_)} AS INTEGER) AS ano,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col_)}) AS municipios_com_vinculo,
            COUNT(DISTINCT {q(cbo_col_)}) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1
        ORDER BY 1
    """)


def complete_municipal_panel(
    counts: pd.DataFrame,
    terr: pd.DataFrame,
    years_selected: list[int],
    pop_mun_df: pd.DataFrame | None,
) -> pd.DataFrame:
    territory_base = terr.copy()
    territory_base = territory_base[
        [
            "cod_municipio",
            "municipio_label",
            "no_municipio",
            "sg_uf",
            "uf",
            "regiao_pais",
            "cod_regiao_de_saude",
            "regiao_de_saude",
            "cod_macrorregiao_de_saude",
            "macrorregiao_de_saude",
            "populacao_ibge_2022",
        ]
    ].drop_duplicates("cod_municipio")

    grid = (
        pd.MultiIndex.from_product(
            [years_selected, territory_base["cod_municipio"].tolist()],
            names=["ano", "cod_municipio"],
        )
        .to_frame(index=False)
        .merge(territory_base, on="cod_municipio", how="left")
    )

    pop_grid = build_population_grid(territory_base, years_selected, pop_mun_df)
    grid = grid.merge(
        pop_grid[
            [
                "ano",
                "cod_municipio",
                "populacao_usada",
                "ano_populacao",
                "fonte_populacao_usada",
                "tipo_populacao",
            ]
        ],
        on=["ano", "cod_municipio"],
        how="left",
    )

    counts2 = counts.copy()
    counts2["cod_municipio"] = counts2["cod_municipio"].astype(str).str[-6:].str.zfill(6)

    panel = grid.merge(counts2, on=["ano", "cod_municipio"], how="left")
    panel["vinculos"] = panel["vinculos"].fillna(0).astype(int)
    panel["ocupacoes_cbo"] = panel["ocupacoes_cbo"].fillna(0).astype(int)
    panel["populacao_usada"] = pd.to_numeric(panel["populacao_usada"], errors="coerce").fillna(0)
    panel["populacao_usada"] = pd.to_numeric(panel["populacao_usada"], errors="coerce").fillna(0)
    panel[f"taxa_{tax_base}"] = panel.apply(
        lambda r: (r["vinculos"] / r["populacao_usada"] * tax_base) if r["populacao_usada"] > 0 else 0,
        axis=1,
    )
    return panel


selected_years = list(range(ano_ini, ano_fim + 1))

series_df = get_series_counts(where_sql, ano_col, municipio_col, cbo_col)

municipal_counts = pd.DataFrame()
municipal_panel = pd.DataFrame()

if territory_filtered is not None:
    municipal_counts = get_municipal_counts(where_sql, ano_col, municipio_col, cbo_col)
    municipal_panel = complete_municipal_panel(municipal_counts, territory_filtered, selected_years, pop_mun)


# ============================================================
# KPIs
# ============================================================

if territory_filtered is not None and not municipal_panel.empty:
    kpi_vinculos = municipal_panel["vinculos"].sum()
    # População média anual usada no denominador, respeitando ano específico/fallback.
    pop_by_year = municipal_panel.groupby("ano")["populacao_usada"].sum()
    kpi_pop = pop_by_year.mean() if not pop_by_year.empty else 0
    kpi_taxa = (kpi_vinculos / (kpi_pop * len(selected_years)) * tax_base) if kpi_pop > 0 and selected_years else 0
    kpi_mun_total = territory_filtered["cod_municipio"].nunique()
    kpi_mun_com_vinc = municipal_panel.loc[municipal_panel["vinculos"] > 0, "cod_municipio"].nunique()
else:
    kpi_vinculos = int(series_df["vinculos"].sum()) if not series_df.empty else 0
    kpi_taxa = None
    kpi_mun_total = None
    kpi_mun_com_vinc = int(series_df["municipios_com_vinculo"].max()) if not series_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vínculos no período", fmt_int(kpi_vinculos))
c2.metric("Municípios com vínculo", fmt_int(kpi_mun_com_vinc))
if kpi_mun_total is not None:
    c3.metric("Municípios no território filtrado", fmt_int(kpi_mun_total))
else:
    c3.metric("CBOs", fmt_int(series_df["ocupacoes_cbo"].max() if not series_df.empty else 0))
if kpi_taxa is not None:
    c4.metric(f"Taxa média — {tax_label}", fmt_float(kpi_taxa, 2))
else:
    c4.metric("Período", f"{ano_ini}–{ano_fim}")


# ============================================================
# ABAS
# ============================================================


if territory_filtered is not None and not municipal_panel.empty:
    pop_status = (
        municipal_panel.groupby(["ano", "tipo_populacao", "ano_populacao"], as_index=False)
        .agg(municipios=("cod_municipio", "nunique"), populacao=("populacao_usada", "sum"))
        .sort_values(["ano", "tipo_populacao", "ano_populacao"])
    )
    with st.expander("Cobertura das populações usadas nos denominadores"):
        st.markdown(
            "As taxas usam população municipal por ano quando disponível. "
            "Para anos sem população municipal exata, o painel usa o ano disponível mais próximo e registra o fallback."
        )
        show_table(pop_status)
        download_buttons(pop_status, "cobertura_populacao_denominadores")

tabs = st.tabs(
    [
        "Visão geral",
        "Taxas per capita e boxplots",
        "Regiões de saúde",
        "Macrorregiões",
        "CBO / especialidades",
        "Panorama salarial",
        "Setor e vínculos",
        "Diagnóstico e exportações",
    ]
)


with tabs[0]:
    st.subheader("Visão geral")

    st.markdown(
        f'<div class="ow-note">A série temporal abaixo usa a tabela bruta `{TABLE}` e preserva todos os anos filtrados. '
        f'Quando a integração territorial está ativa, municípios sem vínculos entram com zero nas visões per capita.</div>',
        unsafe_allow_html=True,
    )

    show_table(series_df)

    left, right = st.columns([1.25, 1])
    with left:
        if not series_df.empty:
            fig = px.line(
                series_df,
                x="ano",
                y="vinculos",
                markers=True,
                title="Vínculos odontológicos por ano",
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

    with right:
        if not series_df.empty:
            fig = px.bar(
                series_df,
                x="ano",
                y="municipios_com_vinculo",
                text="municipios_com_vinculo",
                title="Municípios com vínculo por ano",
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

    download_buttons(series_df, "visao_geral_serie_temporal")


with tabs[1]:
    st.subheader("Taxas per capita e boxplots municipais")

    if territory_filtered is None or municipal_panel.empty:
        st.warning("A visão per capita exige a tabela de regiões com população municipal.")
    else:
        taxa_col = f"taxa_{tax_base}"

        col_a, col_b = st.columns([1.15, 1])
        with col_a:
            fig = px.box(
                municipal_panel,
                x="ano",
                y=taxa_col,
                points="outliers",
                title=f"Distribuição municipal da taxa de profissionais — {tax_label}",
                labels={taxa_col: tax_label, "ano": "Ano"},
            )
            fig.update_xaxes(type="category")
            plot(fig)

        with col_b:
            df_ano_taxa = (
                municipal_panel.groupby("ano", as_index=False)
                .agg(
                    vinculos=("vinculos", "sum"),
                    populacao=("populacao_usada", "sum"),
                    municipios=("cod_municipio", "nunique"),
                    mediana_taxa=(taxa_col, "median"),
                    media_taxa=(taxa_col, "mean"),
                    p75_taxa=(taxa_col, lambda x: x.quantile(0.75)),
                    p25_taxa=(taxa_col, lambda x: x.quantile(0.25)),
                )
            )
            df_ano_taxa["taxa_agregada"] = df_ano_taxa["vinculos"] / df_ano_taxa["populacao"] * tax_base
            show_table(df_ano_taxa)
            download_buttons(df_ano_taxa, "taxas_municipais_resumo_ano")

        st.markdown("### Boxplot por UF")

        fig = px.box(
            municipal_panel,
            x="sg_uf",
            y=taxa_col,
            color="ano",
            points=False,
            title=f"Variação municipal das taxas por UF — {tax_label}",
            labels={"sg_uf": "UF", taxa_col: tax_label},
        )
        plot(fig)

        st.markdown("### Municípios extremos")

        ultimo_ano = max(selected_years)
        mun_last = municipal_panel[municipal_panel["ano"] == ultimo_ano].copy()

        top = mun_last.sort_values(taxa_col, ascending=False).head(30)
        bottom = mun_last.sort_values(taxa_col, ascending=True).head(30)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### Maiores taxas — {ultimo_ano}")
            show_table(top[["ano", "municipio_label", "regiao_de_saude", "macrorregiao_de_saude", "vinculos", "populacao_usada", "ano_populacao", "tipo_populacao", taxa_col]])
            fig = px.bar(top.sort_values(taxa_col), x=taxa_col, y="municipio_label", orientation="h", title=f"Top 30 municípios — {tax_label}")
            plot(fig)

        with c2:
            st.markdown(f"#### Menores taxas — {ultimo_ano}")
            show_table(bottom[["ano", "municipio_label", "regiao_de_saude", "macrorregiao_de_saude", "vinculos", "populacao_usada", "ano_populacao", "tipo_populacao", taxa_col]])

        download_buttons(
            municipal_panel,
            "painel_municipal_taxas",
            {"municipios_taxas": municipal_panel, "resumo_ano": df_ano_taxa},
        )


with tabs[2]:
    st.subheader("Comparações entre regiões de saúde")

    if territory_filtered is None or municipal_panel.empty:
        st.warning("A visão regional exige a tabela de regiões.")
    else:
        taxa_col = f"taxa_{tax_base}"

        region = (
            municipal_panel.groupby(["ano", "cod_regiao_de_saude", "regiao_de_saude", "sg_uf"], as_index=False)
            .agg(
                vinculos=("vinculos", "sum"),
                populacao=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                mediana_municipal=(taxa_col, "median"),
                media_municipal=(taxa_col, "mean"),
            )
        )
        region["taxa_regional"] = region["vinculos"] / region["populacao"] * tax_base

        show_table(region)
        download_buttons(region, "comparacao_regioes_saude")

        c1, c2 = st.columns([1.1, 1])
        with c1:
            fig = px.box(
                region,
                x="ano",
                y="taxa_regional",
                points="all",
                title=f"Distribuição das taxas entre regiões de saúde — {tax_label}",
                labels={"taxa_regional": tax_label},
            )
            fig.update_xaxes(type="category")
            plot(fig)

        with c2:
            last = region[region["ano"] == max(selected_years)].sort_values("taxa_regional", ascending=False).head(30)
            fig = px.bar(
                last.sort_values("taxa_regional"),
                x="taxa_regional",
                y="regiao_de_saude",
                color="sg_uf",
                orientation="h",
                title=f"Top 30 regiões de saúde — {max(selected_years)}",
                labels={"taxa_regional": tax_label},
            )
            plot(fig)

        st.markdown("### Mapa de calor analítico — regiões de saúde")
        top_regions = (
            region.groupby("regiao_de_saude")["vinculos"].sum().sort_values(ascending=False).head(40).index
        )
        heat = region[region["regiao_de_saude"].isin(top_regions)].copy()
        if not heat.empty:
            fig = px.density_heatmap(
                heat,
                x="ano",
                y="regiao_de_saude",
                z="taxa_regional",
                histfunc="avg",
                title=f"Taxa regional nas 40 regiões com mais vínculos — {tax_label}",
                labels={"taxa_regional": tax_label},
            )
            fig.update_xaxes(dtick=1)
            plot(fig)


with tabs[3]:
    st.subheader("Comparações entre macrorregiões de saúde")

    if territory_filtered is None or municipal_panel.empty:
        st.warning("A visão por macrorregião exige a tabela de regiões.")
    else:
        taxa_col = f"taxa_{tax_base}"

        macro = (
            municipal_panel.groupby(["ano", "cod_macrorregiao_de_saude", "macrorregiao_de_saude", "sg_uf"], as_index=False)
            .agg(
                vinculos=("vinculos", "sum"),
                populacao=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                mediana_municipal=(taxa_col, "median"),
                media_municipal=(taxa_col, "mean"),
            )
        )
        macro["taxa_macro"] = macro["vinculos"] / macro["populacao"] * tax_base

        show_table(macro)
        download_buttons(macro, "comparacao_macrorregioes_saude")

        c1, c2 = st.columns([1.1, 1])
        with c1:
            fig = px.box(
                macro,
                x="ano",
                y="taxa_macro",
                points="all",
                title=f"Distribuição das taxas entre macrorregiões — {tax_label}",
                labels={"taxa_macro": tax_label},
            )
            fig.update_xaxes(type="category")
            plot(fig)

        with c2:
            last = macro[macro["ano"] == max(selected_years)].sort_values("taxa_macro", ascending=False).head(30)
            fig = px.bar(
                last.sort_values("taxa_macro"),
                x="taxa_macro",
                y="macrorregiao_de_saude",
                color="sg_uf",
                orientation="h",
                title=f"Top 30 macrorregiões — {max(selected_years)}",
                labels={"taxa_macro": tax_label},
            )
            plot(fig)

        fig = px.line(
            macro,
            x="ano",
            y="taxa_macro",
            color="macrorregiao_de_saude",
            markers=True,
            title=f"Evolução da taxa por macrorregião — {tax_label}",
            labels={"taxa_macro": tax_label},
        )
        fig.update_xaxes(dtick=1)
        plot(fig)


with tabs[4]:
    st.subheader("CBO / especialidades")

    if cbo_desc_col:
        cbo_name_expr = f"ANY_VALUE(CAST({q(cbo_desc_col)} AS VARCHAR)) AS cbo_nome,"
    else:
        cbo_name_expr = f"CAST({q(cbo_col)} AS VARCHAR) AS cbo_nome,"

    cbo_df = sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            CAST({q(cbo_col)} AS VARCHAR) AS cbo,
            {cbo_name_expr}
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
        FROM {TABLE}
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY 1, 4 DESC
    """)

    show_table(cbo_df)
    download_buttons(cbo_df, "cbo_especialidades")

    if not cbo_df.empty:
        top_cbo = cbo_df.groupby("cbo")["vinculos"].sum().sort_values(ascending=False).head(25).index
        top_df = cbo_df[cbo_df["cbo"].isin(top_cbo)].copy()
        top_df["cbo_label"] = top_df["cbo"].astype(str) + " — " + top_df["cbo_nome"].astype(str)

        fig = px.bar(
            top_df,
            x="cbo_label",
            y="vinculos",
            color="ano",
            barmode="group",
            title="Top 25 CBOs por vínculos",
        )
        plot(fig)

        fig = px.line(
            top_df,
            x="ano",
            y="vinculos",
            color="cbo_label",
            markers=True,
            title="Evolução temporal dos principais CBOs",
        )
        fig.update_xaxes(dtick=1)
        plot(fig)


with tabs[5]:
    st.subheader("Panorama salarial")

    if not salario_cols:
        st.warning("Nenhuma coluna salarial detectada na tabela.")
    else:
        diagnostics = []
        for col in salario_cols:
            expr = numeric_expr(col)
            d = sql_df(f"""
                SELECT
                    '{col}' AS coluna,
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    COUNT(*) AS registros,
                    SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS validos,
                    AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS media
                FROM {TABLE}
                WHERE {where_sql}
                GROUP BY 1, 2
                ORDER BY 2
            """)
            diagnostics.append(d)

        diag = pd.concat(diagnostics, ignore_index=True)
        show_table(diag)
        best_col = diag.groupby("coluna")["validos"].sum().sort_values(ascending=False).index[0]
        expr = numeric_expr(best_col)

        st.markdown(
            f'<div class="ow-note">Coluna salarial usada: <b>{best_col}</b>. '
            f'As demais permanecem no diagnóstico para checagem de completude.</div>',
            unsafe_allow_html=True,
        )

        sal_year = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS registros_validos,
                AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_media,
                MEDIAN(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_mediana,
                QUANTILE_CONT(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END, 0.25) AS p25,
                QUANTILE_CONT(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END, 0.75) AS p75
            FROM {TABLE}
            WHERE {where_sql}
            GROUP BY 1
            ORDER BY 1
        """)

        show_table(sal_year)

        plot_df = sal_year.dropna(subset=["remuneracao_media"])
        if not plot_df.empty:
            fig = px.line(
                plot_df,
                x="ano",
                y=["remuneracao_media", "remuneracao_mediana", "p25", "p75"],
                markers=True,
                title="Remuneração — média, mediana e quartis",
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

        if uf_col_db:
            sal_uf = sql_df(f"""
                SELECT
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    CAST({q(uf_col_db)} AS VARCHAR) AS uf,
                    SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS registros_validos,
                    AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_media
                FROM {TABLE}
                WHERE {where_sql}
                GROUP BY 1, 2
                HAVING registros_validos >= 20
                ORDER BY 1, 4 DESC
            """)
            if not sal_uf.empty:
                fig = px.box(
                    sal_uf,
                    x="ano",
                    y="remuneracao_media",
                    points="all",
                    title="Variação da remuneração média entre UFs",
                )
                fig.update_xaxes(type="category")
                plot(fig)

        download_buttons(sal_year, "panorama_salarial", {"salario_ano": sal_year, "diagnostico_salario": diag})


with tabs[6]:
    st.subheader("Setor e vínculos")

    if not setor_col:
        st.warning("Nenhuma coluna de setor detectada.")
    else:
        setor = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                CAST({q(setor_col)} AS VARCHAR) AS setor,
                COUNT(*) AS vinculos,
                COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios,
                COUNT(DISTINCT {q(cbo_col)}) AS ocupacoes_cbo
            FROM {TABLE}
            WHERE {where_sql}
              AND {q(setor_col)} IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
        """)

        show_table(setor)
        download_buttons(setor, "setor_vinculos")

        if not setor.empty:
            top_setor = setor.groupby("setor")["vinculos"].sum().sort_values(ascending=False).head(20).index
            top = setor[setor["setor"].isin(top_setor)]

            fig = px.bar(
                top,
                x="setor",
                y="vinculos",
                color="ano",
                barmode="group",
                title="Top 20 setores por vínculos",
            )
            plot(fig)


with tabs[7]:
    st.subheader("Diagnóstico e exportações")

    st.markdown(
        '<div class="ow-note">Esta aba reúne tabelas consolidadas para auditoria. '
        'Use os botões para baixar CSV ou Excel com múltiplas abas.</div>',
        unsafe_allow_html=True,
    )

    show_table(series_df)

    desc = pd.DataFrame({"coluna": cols})
    show_table(desc)

    exports: dict[str, pd.DataFrame] = {
        "serie_temporal": series_df,
        "colunas": desc,
    }

    if not municipal_panel.empty:
        exports["municipios_taxas"] = municipal_panel
    if territory_filtered is not None:
        exports["territorio_filtrado"] = territory_filtered
    if pop_mun is not None:
        exports["populacao_municipal"] = pop_mun
    if pop_uf is not None:
        exports["populacao_uf"] = pop_uf

    download_buttons(series_df, "exportacao_geral_dashboard", exports)
