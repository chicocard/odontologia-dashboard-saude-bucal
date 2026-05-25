
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
DB_PATH = Path(r"C:\rais-intelligence-data\database\odontologia_workforce.duckdb")
TABLE = "odontologia_vinculos"

REFERENCE_DIRS = [
    APP_DIR / "reference",
    ROOT_DIR / "reference",
    APP_DIR,
]

TERRITORY_NAMES = ["tabela_regioes(1).csv", "tabela_regioes.csv"]
POP_NAMES = ["populacao_tcu_municipios.csv", "populacao_municipios.csv"]
CBO_MAP_NAMES = ["cbo_odontologia_mapa.csv", "cbo_mapa.csv"]

st.set_page_config(
    page_title="OdontoWorkforce Brasil — V5",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CSS / TEMA VISUAL
# =============================================================================

st.markdown(
    """
    <style>
    :root {
        --ow-bg: #f6f8fb;
        --ow-card: #ffffff;
        --ow-border: #e4eaf2;
        --ow-text: #0f172a;
        --ow-muted: #64748b;
        --ow-blue: #1d4ed8;
        --ow-cyan: #0891b2;
        --ow-green: #047857;
        --ow-orange: #c2410c;
    }

    .block-container {
        padding-top: 0.85rem;
        padding-bottom: 2.5rem;
        max-width: 1540px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e5e7eb;
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label {
        font-size: 0.90rem;
    }

    .ow-hero {
        background: linear-gradient(135deg, #0f172a 0%, #164e63 52%, #0369a1 100%);
        color: white;
        border-radius: 1.25rem;
        padding: 1.25rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 35px rgba(15, 23, 42, 0.22);
    }

    .ow-hero-title {
        font-size: 2.05rem;
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: -0.045em;
        margin-bottom: 0.2rem;
    }

    .ow-hero-subtitle {
        color: #dbeafe;
        font-size: 1.03rem;
        margin-top: 0.25rem;
    }

    .ow-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin-top: .85rem;
    }

    .ow-chip {
        border-radius: 999px;
        padding: .28rem .62rem;
        background: rgba(255,255,255,.12);
        border: 1px solid rgba(255,255,255,.20);
        color: #e0f2fe;
        font-size: .86rem;
    }

    .ow-section-title {
        font-size: 1.28rem;
        font-weight: 780;
        letter-spacing: -0.02em;
        margin: .2rem 0 .55rem 0;
        color: #0f172a;
    }

    .ow-note {
        border: 1px solid var(--ow-border);
        background: #f8fafc;
        color: #334155;
        padding: .8rem .95rem;
        border-radius: 1rem;
        margin: .55rem 0 .9rem 0;
    }

    .ow-warning {
        border: 1px solid #fed7aa;
        background: #fff7ed;
        color: #9a3412;
        padding: .8rem .95rem;
        border-radius: 1rem;
        margin: .55rem 0 .9rem 0;
    }

    .ow-small {
        color: #64748b;
        font-size: .88rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #e6edf5;
        padding: 1rem 1.05rem;
        border-radius: 1.12rem;
        box-shadow: 0 6px 22px rgba(15, 23, 42, 0.07);
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.62rem;
        font-weight: 850;
        letter-spacing: -0.03em;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: .35rem;
        border-bottom: 0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        padding: .48rem .85rem;
        background: #f1f5f9;
        color: #334155;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: #0f172a !important;
        color: white !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        overflow: hidden;
        background: #ffffff;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #edf2f7;
        border-radius: .95rem;
        overflow: hidden;
    }

    .ow-footer {
        color: #64748b;
        font-size: .84rem;
        margin-top: .65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

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


def find_reference_file(names: list[str]) -> Path | None:
    for refdir in REFERENCE_DIRS:
        for name in names:
            p = refdir / name
            if p.exists():
                return p
    return None


def pick(cols: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def mun_key_expr(col: str) -> str:
    return f"""
    RIGHT(
        '000000' || REGEXP_REPLACE(CAST({q(col)} AS VARCHAR), '[^0-9]', '', 'g'),
        6
    )
    """


def numeric_expr(col: str) -> str:
    return f"""
    COALESCE(
        TRY_CAST({q(col)} AS DOUBLE),
        TRY_CAST(REPLACE(CAST({q(col)} AS VARCHAR), ',', '.') AS DOUBLE),
        TRY_CAST(REPLACE(REPLACE(CAST({q(col)} AS VARCHAR), '.', ''), ',', '.') AS DOUBLE)
    )
    """


def make_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    seen: dict[str, int] = {}
    new_cols: list[str] = []

    for col in out.columns:
        base = str(col)
        if base in seen:
            seen[base] += 1
            new_cols.append(f"{base} ({seen[base] + 1})")
        else:
            seen[base] = 0
            new_cols.append(base)

    out.columns = new_cols
    return out


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = name[:31].replace("/", "_").replace("\\", "_")
            make_unique_columns(df).to_excel(writer, index=False, sheet_name=safe)
    return output.getvalue()


def download_buttons(df: pd.DataFrame, base_name: str, sheets: dict[str, pd.DataFrame] | None = None):
    data = make_unique_columns(df)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ CSV",
            data=data.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{base_name}.csv",
            mime="text/csv",
            key=f"{base_name}_csv",
            width="stretch",
        )
    with c2:
        st.download_button(
            "⬇️ Excel",
            data=excel_bytes(sheets if sheets else {"dados": data}),
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{base_name}_xlsx",
            width="stretch",
        )


def show_table(df: pd.DataFrame, height: int | str | None = None, max_rows: int | None = None):
    display = make_unique_columns(df.copy())
    if max_rows is not None:
        display = display.head(max_rows).copy()

    kwargs = {"hide_index": True}
    if height is not None:
        kwargs["height"] = height

    try:
        st.dataframe(display, width="stretch", **kwargs)
    except TypeError:
        st.dataframe(display, use_container_width=True, **kwargs)


def plot(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(size=13),
        title=dict(font=dict(size=18), x=0.02, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=20, r=25, t=75, b=35),
    )
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# DICIONÁRIOS DE NOMES LEGÍVEIS
# =============================================================================

SEX_MAP = {
    "1": "Masculino",
    "2": "Feminino",
    "M": "Masculino",
    "F": "Feminino",
    "Masculino": "Masculino",
    "Feminino": "Feminino",
}

RACA_MAP = {
    "1": "Indígena",
    "2": "Branca",
    "4": "Preta",
    "6": "Amarela",
    "8": "Parda",
    "9": "Não informado",
    "-1": "Não informado",
    "0": "Não informado",
}

TIPO_VINCULO_MAP = {
    "10": "CLT — pessoa jurídica, prazo indeterminado",
    "15": "CLT — pessoa física, prazo indeterminado",
    "20": "CLT — pessoa jurídica, prazo determinado",
    "25": "CLT — pessoa física, prazo determinado",
    "30": "Servidor estatutário",
    "31": "Servidor estatutário — RGPS",
    "35": "Servidor público não efetivo",
    "40": "Trabalhador avulso",
    "50": "Trabalhador temporário",
    "55": "Aprendiz",
    "60": "Contrato por prazo determinado",
    "70": "Diretor sem vínculo empregatício",
    "75": "Diretor sem vínculo empregatício — sem FGTS",
    "80": "Contrato especial / prazo determinado",
    "90": "Outros vínculos",
}

NATUREZA_GRUPO_MAP = {
    "1": "Administração pública",
    "2": "Entidades empresariais",
    "3": "Entidades sem fins lucrativos",
    "4": "Pessoas físicas",
    "5": "Organizações internacionais / extraterritoriais",
}

CNAE_DIVISAO_MAP = {
    "84": "Administração pública, defesa e seguridade social",
    "85": "Educação",
    "86": "Atividades de atenção à saúde humana",
    "87": "Atenção residencial à saúde",
    "88": "Assistência social",
    "94": "Organizações associativas",
    "96": "Outras atividades de serviços pessoais",
}

COLUMN_LABELS = {
    "ano": "Ano",
    "cod_municipio": "Código IBGE do município",
    "municipio": "Município",
    "municipio_label": "Município",
    "no_municipio": "Município",
    "sg_uf": "UF",
    "uf": "Estado",
    "regiao_de_saude": "Região de saúde",
    "macrorregiao_de_saude": "Macrorregião de saúde",
    "populacao": "População",
    "populacao_usada": "População usada",
    "ano_populacao": "Ano da população",
    "fonte_populacao": "Fonte da população",
    "vinculos": "Vínculos",
    "municipios": "Municípios",
    "municipios_com_vinculo": "Municípios com vínculo",
    "ocupacoes_cbo": "Ocupações CBO",
    "taxa": "Taxa",
    "taxa_municipal": "Taxa municipal",
    "taxa_regional": "Taxa regional",
    "taxa_macro": "Taxa da macrorregião",
    "cbo": "CBO",
    "cbo_nome": "Especialidade / ocupação",
    "cbo_label": "Especialidade / ocupação",
    "grupo_ocupacional": "Grupo ocupacional",
    "familia_especialidade": "Família de especialidade",
    "sexo": "Sexo",
    "raca_cor": "Raça/cor",
    "setor": "Setor / vínculo",
    "categoria": "Categoria",
    "categoria_original": "Categoria original",
    "remuneracao_media": "Remuneração média",
    "remuneracao_mediana": "Remuneração mediana",
    "p25": "P25",
    "p75": "P75",
}


def friendly_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [COLUMN_LABELS.get(str(c), str(c).replace("_", " ").title()) for c in out.columns]
    return make_unique_columns(out)


def normalize_code(value: Any, width: int | None = None) -> str:
    if pd.isna(value):
        return ""
    s = "".join(ch for ch in str(value) if ch.isdigit())
    if width and s:
        s = s.zfill(width)
    return s


def decode_sex(value: Any) -> str:
    raw = str(value).strip()
    code = normalize_code(value)
    return SEX_MAP.get(raw, SEX_MAP.get(code, raw.title() if raw else "Não informado"))


def decode_race(value: Any) -> str:
    raw = str(value).strip()
    code = normalize_code(value)
    return RACA_MAP.get(raw, RACA_MAP.get(code, raw.title() if raw else "Não informado"))


def decode_tipo_vinculo(value: Any) -> str:
    code = normalize_code(value)
    key = code[:2] if len(code) >= 2 else code.zfill(2)
    return TIPO_VINCULO_MAP.get(key, f"Tipo de vínculo {key}" if key else "Não informado")


def decode_natureza_grupo(value: Any) -> str:
    code = normalize_code(value)
    if code:
        return NATUREZA_GRUPO_MAP.get(code[0], f"Grupo natureza jurídica {code[0]}")
    raw = str(value).strip()
    return raw.title() if raw else "Não informado"


def decode_natureza_detalhe(value: Any) -> str:
    code = normalize_code(value)
    if code:
        return f"{code} — {decode_natureza_grupo(code)}"
    raw = str(value).strip()
    return raw.title() if raw else "Não informado"


def decode_cnae(value: Any) -> str:
    code = normalize_code(value)
    if code:
        div = code[:2]
        return CNAE_DIVISAO_MAP.get(div, f"CNAE divisão {div}")
    raw = str(value).strip()
    return raw.title() if raw else "Não informado"


# =============================================================================
# LEITURA DE REFERÊNCIAS
# =============================================================================

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
def load_territory() -> tuple[pd.DataFrame | None, str]:
    path = find_reference_file(TERRITORY_NAMES)
    if path is None:
        return None, ""

    df = pd.read_csv(path, sep=";", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    required = [
        "sg_uf",
        "uf",
        "cod_municipio",
        "no_municipio",
        "regiao_de_saude",
        "macrorregiao_de_saude",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, f"{path} sem colunas: {missing}"

    df["cod_municipio"] = (
        df["cod_municipio"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    )
    df["municipio_nome_limpo"] = (
        df["no_municipio"].astype(str).str.replace(r"^[A-Z]{2}\s*-\s*", "", regex=True).str.title()
    )
    df["municipio_label"] = df["sg_uf"].astype(str) + " — " + df["municipio_nome_limpo"]

    if "populacao_ibge_2022" in df.columns:
        df["populacao_ibge_2022"] = pd.to_numeric(df["populacao_ibge_2022"], errors="coerce")
    else:
        df["populacao_ibge_2022"] = pd.NA

    df = df.drop_duplicates("cod_municipio").copy()
    return df, str(path)


@st.cache_data(show_spinner=False)
def load_population() -> tuple[pd.DataFrame | None, str]:
    path = find_reference_file(POP_NAMES)
    if path is None:
        return None, ""

    df = pd.read_csv(path, sep=None, engine="python", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    code_col = pick(df.columns.tolist(), ["cod_municipio", "codigo_municipio", "co_municipio", "municipio_codigo"])
    year_col = pick(df.columns.tolist(), ["ano", "year"])
    pop_col = pick(df.columns.tolist(), ["populacao", "população", "populacao_estimada", "estimativa", "pop"])

    if code_col and year_col and pop_col:
        out = df[[code_col, year_col, pop_col]].copy()
        out.columns = ["cod_municipio", "ano", "populacao"]
    else:
        year_cols = [c for c in df.columns if str(c).isdigit() and 1900 <= int(c) <= 2100]
        if not code_col or not year_cols:
            return None, f"{path} sem estrutura municipal reconhecida."
        out = df.melt(id_vars=[code_col], value_vars=year_cols, var_name="ano", value_name="populacao")
        out = out.rename(columns={code_col: "cod_municipio"})

    out["cod_municipio"] = out["cod_municipio"].astype(str).str.replace(r"\D", "", regex=True).str[-6:].str.zfill(6)
    out["ano"] = pd.to_numeric(out["ano"], errors="coerce").astype("Int64")
    out["populacao"] = (
        out["populacao"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    out["populacao"] = pd.to_numeric(out["populacao"], errors="coerce")
    out = out.dropna(subset=["cod_municipio", "ano", "populacao"]).copy()
    out["ano"] = out["ano"].astype(int)
    out = out.groupby(["cod_municipio", "ano"], as_index=False)["populacao"].max()
    return out, str(path)


@st.cache_data(show_spinner=False)
def load_cbo_map() -> tuple[pd.DataFrame, str]:
    path = find_reference_file(CBO_MAP_NAMES)

    if path is not None:
        df = pd.read_csv(path, sep=None, engine="python", dtype=str)
        df.columns = [str(c).strip() for c in df.columns]

        cbo_col = pick(df.columns.tolist(), ["cbo", "codigo_cbo", "CBO"])
        nome_col = pick(df.columns.tolist(), ["cbo_nome", "nome", "ocupacao", "especialidade", "descricao"])
        grupo_col = pick(df.columns.tolist(), ["grupo_ocupacional", "grupo"])
        familia_col = pick(df.columns.tolist(), ["familia_especialidade", "familia", "categoria"])

        if cbo_col:
            out = pd.DataFrame()
            out["cbo"] = df[cbo_col].astype(str).str.replace(r"\D", "", regex=True)
            out["cbo_nome"] = df[nome_col].astype(str) if nome_col else out["cbo"]
            out["grupo_ocupacional"] = df[grupo_col].astype(str) if grupo_col else "Odontologia"
            out["familia_especialidade"] = df[familia_col].astype(str) if familia_col else "Odontologia"
            out = out.drop_duplicates("cbo")
            return out, str(path)

    # fallback mínimo editável pelo usuário
    fallback = pd.DataFrame(
        [
            ["223208", "Cirurgião-dentista — clínico geral", "Cirurgiões-dentistas", "Clínica odontológica"],
            ["223212", "Cirurgião-dentista — auditor", "Cirurgiões-dentistas", "Auditoria"],
            ["223216", "Cirurgião-dentista — dentística", "Cirurgiões-dentistas", "Dentística"],
            ["223220", "Cirurgião-dentista — disfunção temporomandibular e dor orofacial", "Cirurgiões-dentistas", "Dor orofacial / DTM"],
            ["223224", "Cirurgião-dentista — endodontista", "Cirurgiões-dentistas", "Endodontia"],
            ["223228", "Cirurgião-dentista — estomatologista", "Cirurgiões-dentistas", "Estomatologia"],
            ["223232", "Cirurgião-dentista — implantodontista", "Cirurgiões-dentistas", "Implantodontia"],
            ["223236", "Cirurgião-dentista — odontogeriatra", "Cirurgiões-dentistas", "Odontogeriatria"],
            ["223240", "Cirurgião-dentista — odontologia do trabalho", "Cirurgiões-dentistas", "Odontologia do trabalho"],
            ["223244", "Cirurgião-dentista — odontologia para pacientes com necessidades especiais", "Cirurgiões-dentistas", "Pacientes especiais"],
            ["223248", "Cirurgião-dentista — odontopediatra", "Cirurgiões-dentistas", "Odontopediatria"],
            ["223252", "Cirurgião-dentista — ortopedista e ortodontista", "Cirurgiões-dentistas", "Ortodontia / ortopedia"],
            ["223256", "Cirurgião-dentista — patologista bucal", "Cirurgiões-dentistas", "Patologia bucal"],
            ["223260", "Cirurgião-dentista — periodontista", "Cirurgiões-dentistas", "Periodontia"],
            ["223264", "Cirurgião-dentista — protesiólogo bucomaxilofacial", "Cirurgiões-dentistas", "Prótese bucomaxilofacial"],
            ["223268", "Cirurgião-dentista — protesista", "Cirurgiões-dentistas", "Prótese dentária"],
            ["223272", "Cirurgião-dentista — radiologista", "Cirurgiões-dentistas", "Radiologia odontológica"],
            ["223276", "Cirurgião-dentista — saúde coletiva", "Cirurgiões-dentistas", "Saúde coletiva"],
            ["223280", "Cirurgião-dentista — traumatologista bucomaxilofacial", "Cirurgiões-dentistas", "Cirurgia bucomaxilofacial"],
            ["322405", "Técnico em saúde bucal", "Equipe auxiliar odontológica", "Técnico em saúde bucal"],
            ["322415", "Auxiliar em saúde bucal", "Equipe auxiliar odontológica", "Auxiliar em saúde bucal"],
            ["322420", "Auxiliar de prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"],
            ["322425", "Técnico em prótese dentária", "Equipe auxiliar odontológica", "Prótese dentária"],
        ],
        columns=["cbo", "cbo_nome", "grupo_ocupacional", "familia_especialidade"],
    )
    return fallback, "fallback interno"


@st.cache_data(show_spinner=False)
def get_years(ano_col: str) -> list[int]:
    df = sql_df(f"""
        SELECT DISTINCT CAST({q(ano_col)} AS INTEGER) AS ano
        FROM {TABLE}
        WHERE {q(ano_col)} IS NOT NULL
        ORDER BY 1
    """)
    return df["ano"].dropna().astype(int).tolist()


@st.cache_data(show_spinner=True)
def base_cbo_counts(ano_col: str, cbo_col: str, where_without_cbo: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(cbo_col)} AS VARCHAR) AS cbo,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT CAST({q(ano_col)} AS INTEGER)) AS anos_com_dado
        FROM {TABLE}
        WHERE {where_without_cbo}
          AND {q(cbo_col)} IS NOT NULL
        GROUP BY 1
        ORDER BY vinculos DESC
    """)


# =============================================================================
# VALIDAÇÃO
# =============================================================================

st.markdown(
    """
    <div class="ow-hero">
        <div class="ow-hero-title">OdontoWorkforce Brasil</div>
        <div class="ow-hero-subtitle">
            Painel V5 — força de trabalho odontológica, território, especialidades, vínculos e taxas per capita.
        </div>
        <div class="ow-chip-row">
            <span class="ow-chip">RAIS</span>
            <span class="ow-chip">Municípios</span>
            <span class="ow-chip">Regiões de Saúde</span>
            <span class="ow-chip">Macrorregiões</span>
            <span class="ow-chip">CBO / Especialidades</span>
            <span class="ow-chip">Exportação CSV/Excel</span>
        </div>
    </div>
    """,
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
uf_col_db = pick(cols, ["uf_nome", "uf", "uf_sigla", "sg_uf"])
sexo_col = pick(cols, ["sexo", "sexo_trabalhador", "Sexo Trabalhador"])
raca_col = pick(cols, ["raca_cor", "raça_cor", "raca", "Raça Cor"])
tipo_vinculo_col = pick(cols, ["tipo_vinculo", "Tipo Vínculo"])
natureza_col = pick(cols, ["natureza_juridica", "Natureza Jurídica"])
cnae_col = pick(cols, ["cnae_divisao", "cnae", "CNAE 2.0 Classe"])
idade_col = pick(cols, ["idade", "Idade"])
horas_col = pick(cols, ["horas_semanais", "qtd_hora_contr", "Qtd Hora Contr"])
salario_cols = [c for c in ["remuneracao_media_mensal", "remuneracao_hora", "remun_media", "vl_remun_media_nom", "Vl Remun Média Nom"] if c in cols]

if not all([ano_col, municipio_col, cbo_col]):
    st.error(f"Colunas essenciais não detectadas: ano={ano_col}, município={municipio_col}, CBO={cbo_col}")
    st.stop()

territory, territory_path = load_territory()
population, population_path = load_population()
cbo_map, cbo_map_path = load_cbo_map()

cbo_map["cbo"] = cbo_map["cbo"].astype(str).str.replace(r"\D", "", regex=True)


# =============================================================================
# FILTROS ORGANIZADOS
# =============================================================================

st.sidebar.markdown("## Painel de seleção")
st.sidebar.caption("Deixe uma seleção vazia para não restringir aquela dimensão.")

years = get_years(ano_col)
with st.sidebar.expander("1. Período", expanded=True):
    ano_ini, ano_fim = st.slider(
        "Anos",
        min_value=min(years),
        max_value=max(years),
        value=(min(years), max(years)),
        step=1,
        help="O painel usa apenas os anos efetivamente existentes no banco.",
    )
    selected_years = list(range(ano_ini, ano_fim + 1))

where_parts = [f"CAST({q(ano_col)} AS INTEGER) BETWEEN {ano_ini} AND {ano_fim}"]

territory_filtered = territory.copy() if territory is not None else None

with st.sidebar.expander("2. Território", expanded=True):
    if territory_filtered is None:
        st.warning("Tabela de regiões não localizada.")
    else:
        uf_options = territory_filtered["sg_uf"].dropna().sort_values().unique().tolist()
        uf_selected = st.multiselect("UF", uf_options, default=[], help="Vazio = todas as UFs.")

        if uf_selected:
            territory_filtered = territory_filtered[territory_filtered["sg_uf"].isin(uf_selected)].copy()

        macro_options = territory_filtered["macrorregiao_de_saude"].dropna().sort_values().unique().tolist()
        macro_selected = st.multiselect("Macrorregião de saúde", macro_options, default=[], help="Vazio = todas.")

        if macro_selected:
            territory_filtered = territory_filtered[territory_filtered["macrorregiao_de_saude"].isin(macro_selected)].copy()

        reg_options = territory_filtered["regiao_de_saude"].dropna().sort_values().unique().tolist()
        reg_selected = st.multiselect("Região de saúde", reg_options, default=[], help="Vazio = todas.")

        if reg_selected:
            territory_filtered = territory_filtered[territory_filtered["regiao_de_saude"].isin(reg_selected)].copy()

        municipality_limit = st.toggle("Filtrar municípios específicos", value=False)
        if municipality_limit:
            mun_options = territory_filtered[["cod_municipio", "municipio_label"]].drop_duplicates().sort_values("municipio_label")
            mun_label_to_code = dict(zip(mun_options["municipio_label"], mun_options["cod_municipio"]))
            mun_labels = st.multiselect("Municípios", mun_options["municipio_label"].tolist(), default=[])
            if mun_labels:
                territory_filtered = territory_filtered[territory_filtered["cod_municipio"].isin([mun_label_to_code[x] for x in mun_labels])].copy()

        if len(territory_filtered) < len(territory):
            codes = territory_filtered["cod_municipio"].dropna().astype(str).unique().tolist()
            if codes:
                where_parts.append(f"{mun_key_expr(municipio_col)} IN ({','.join(lit(x) for x in codes)})")

where_without_cbo = " AND ".join(where_parts)

with st.sidebar.expander("3. Especialidades / CBO", expanded=True):
    cbo_counts = base_cbo_counts(ano_col, cbo_col, where_without_cbo)
    cbo_counts["cbo"] = cbo_counts["cbo"].astype(str).str.replace(r"\D", "", regex=True)
    cbo_options = cbo_counts.merge(cbo_map, on="cbo", how="left")
    cbo_options["cbo_nome"] = cbo_options["cbo_nome"].fillna("CBO " + cbo_options["cbo"])
    cbo_options["grupo_ocupacional"] = cbo_options["grupo_ocupacional"].fillna("Outras ocupações odontológicas")
    cbo_options["familia_especialidade"] = cbo_options["familia_especialidade"].fillna("Não classificada")
    cbo_options["label"] = (
        cbo_options["cbo_nome"].astype(str)
        + " — "
        + cbo_options["cbo"].astype(str)
        + " ("
        + cbo_options["vinculos"].map(fmt_int)
        + ")"
    )

    grupos = sorted(cbo_options["grupo_ocupacional"].dropna().unique().tolist())
    selected_grupos = st.multiselect("Grupo ocupacional", grupos, default=[], help="Vazio = todos.")
    cbo_filtered = cbo_options.copy()
    if selected_grupos:
        cbo_filtered = cbo_filtered[cbo_filtered["grupo_ocupacional"].isin(selected_grupos)].copy()

    familias = sorted(cbo_filtered["familia_especialidade"].dropna().unique().tolist())
    selected_familias = st.multiselect("Família de especialidade", familias, default=[], help="Vazio = todas.")
    if selected_familias:
        cbo_filtered = cbo_filtered[cbo_filtered["familia_especialidade"].isin(selected_familias)].copy()

    search_text = st.text_input("Buscar CBO ou especialidade", placeholder="Ex.: endodontia, técnico, prótese...")
    if search_text.strip():
        s = search_text.strip().lower()
        cbo_filtered = cbo_filtered[
            cbo_filtered["label"].str.lower().str.contains(s, regex=False)
            | cbo_filtered["grupo_ocupacional"].str.lower().str.contains(s, regex=False)
            | cbo_filtered["familia_especialidade"].str.lower().str.contains(s, regex=False)
        ].copy()

    selection_mode = st.radio(
        "Modo de seleção",
        ["Todos filtrados", "Top N", "Escolha manual"],
        horizontal=False,
    )

    if selection_mode == "Top N":
        top_n_cbo = st.slider("Top N CBOs", 1, min(60, max(1, len(cbo_filtered))), min(15, max(1, len(cbo_filtered))))
        selected_cbos = cbo_filtered.head(top_n_cbo)["cbo"].tolist()
    elif selection_mode == "Escolha manual":
        label_to_cbo = dict(zip(cbo_filtered["label"], cbo_filtered["cbo"]))
        selected_labels = st.multiselect("Selecionar CBOs", cbo_filtered["label"].tolist(), default=[])
        selected_cbos = [label_to_cbo[x] for x in selected_labels]
    else:
        selected_cbos = cbo_filtered["cbo"].tolist()

    if selected_cbos and len(selected_cbos) < len(cbo_options):
        where_parts.append(f"REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') IN ({','.join(lit(x) for x in selected_cbos)})")

with st.sidebar.expander("4. Perfil e vínculo", expanded=False):
    if sexo_col:
        sexo_raw = sql_df(f"""
            SELECT DISTINCT CAST({q(sexo_col)} AS VARCHAR) AS v
            FROM {TABLE}
            WHERE {where_without_cbo}
              AND {q(sexo_col)} IS NOT NULL
            ORDER BY 1
        """)["v"].dropna().tolist()
        sexo_labels = {decode_sex(x): x for x in sexo_raw}
        selected_sex_labels = st.multiselect("Sexo", sorted(sexo_labels), default=[])
        if selected_sex_labels:
            where_parts.append(f"CAST({q(sexo_col)} AS VARCHAR) IN ({','.join(lit(sexo_labels[x]) for x in selected_sex_labels)})")

    if raca_col:
        raca_raw = sql_df(f"""
            SELECT DISTINCT CAST({q(raca_col)} AS VARCHAR) AS v
            FROM {TABLE}
            WHERE {where_without_cbo}
              AND {q(raca_col)} IS NOT NULL
            ORDER BY 1
        """)["v"].dropna().tolist()
        raca_labels = {decode_race(x): x for x in raca_raw}
        selected_raca_labels = st.multiselect("Raça/cor", sorted(raca_labels), default=[])
        if selected_raca_labels:
            where_parts.append(f"CAST({q(raca_col)} AS VARCHAR) IN ({','.join(lit(raca_labels[x]) for x in selected_raca_labels)})")

    setor_filter_col = tipo_vinculo_col or natureza_col or cnae_col
    if setor_filter_col:
        raw_vals = sql_df(f"""
            SELECT DISTINCT CAST({q(setor_filter_col)} AS VARCHAR) AS v
            FROM {TABLE}
            WHERE {where_without_cbo}
              AND {q(setor_filter_col)} IS NOT NULL
            ORDER BY 1
        """)["v"].dropna().head(200).tolist()
        selected_setor_raw = st.multiselect("Vínculo/setor original", raw_vals, default=[])
        if selected_setor_raw:
            where_parts.append(f"CAST({q(setor_filter_col)} AS VARCHAR) IN ({','.join(lit(x) for x in selected_setor_raw)})")

with st.sidebar.expander("5. Apresentação", expanded=False):
    tax_base = st.selectbox("Base da taxa", [10_000, 100_000], index=0)
    max_categories = st.slider("Categorias por gráfico", 8, 40, 20, step=4)
    show_raw_tables = st.toggle("Mostrar tabelas detalhadas", value=True)

tax_label = f"vínculos por {tax_base:,} hab.".replace(",", ".")
where_sql = " AND ".join(where_parts)

st.sidebar.markdown("---")
st.sidebar.caption("Referências carregadas")
st.sidebar.write(f"Regiões: `{Path(territory_path).name if territory_path else 'não carregada'}`")
st.sidebar.write(f"População: `{Path(population_path).name if population_path else 'fallback/2022'}`")
st.sidebar.write(f"CBO: `{Path(cbo_map_path).name if cbo_map_path and cbo_map_path != 'fallback interno' else cbo_map_path}`")


# =============================================================================
# CONSULTAS E PAINÉIS
# =============================================================================

@st.cache_data(show_spinner=True)
def get_series(where_sql_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios_com_vinculo,
            COUNT(DISTINCT REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g')) AS ocupacoes_cbo
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
            COUNT(DISTINCT REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g')) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)


def build_population_panel(terr: pd.DataFrame, counts: pd.DataFrame, years_selected: list[int]) -> pd.DataFrame:
    base_territory = terr[
        [
            "cod_municipio",
            "municipio_label",
            "no_municipio",
            "sg_uf",
            "uf",
            "regiao_de_saude",
            "macrorregiao_de_saude",
            "populacao_ibge_2022",
        ]
    ].drop_duplicates("cod_municipio").copy()

    grid = (
        pd.MultiIndex.from_product(
            [years_selected, base_territory["cod_municipio"].tolist()],
            names=["ano", "cod_municipio"],
        )
        .to_frame(index=False)
        .merge(base_territory, on="cod_municipio", how="left")
    )

    counts2 = counts.copy()
    counts2["cod_municipio"] = counts2["cod_municipio"].astype(str).str[-6:].str.zfill(6)
    panel = grid.merge(counts2, on=["ano", "cod_municipio"], how="left")
    panel["vinculos"] = panel["vinculos"].fillna(0).astype(int)
    panel["ocupacoes_cbo"] = panel["ocupacoes_cbo"].fillna(0).astype(int)

    if population is not None and not population.empty:
        pop = population.copy()
        panel = panel.merge(pop, on=["cod_municipio", "ano"], how="left")
        panel = panel.rename(columns={"populacao": "populacao_exata"})
    else:
        panel["populacao_exata"] = pd.NA

    panel["populacao_fallback_2022"] = pd.to_numeric(panel["populacao_ibge_2022"], errors="coerce")
    panel["populacao_usada"] = panel["populacao_exata"].fillna(panel["populacao_fallback_2022"])
    panel["tipo_populacao"] = panel["populacao_exata"].notna().map({True: "População do ano", False: "Fallback 2022"})
    panel["taxa_municipal"] = panel.apply(
        lambda r: (r["vinculos"] / r["populacao_usada"] * tax_base) if pd.notna(r["populacao_usada"]) and r["populacao_usada"] > 0 else 0,
        axis=1,
    )
    return panel


series_df = get_series(where_sql)
municipal_counts = pd.DataFrame()
municipal_panel = pd.DataFrame()

if territory_filtered is not None and not territory_filtered.empty:
    municipal_counts = get_municipal_counts(where_sql)
    municipal_panel = build_population_panel(territory_filtered, municipal_counts, selected_years)


# =============================================================================
# KPIs
# =============================================================================

if not series_df.empty:
    total_vinc = int(series_df["vinculos"].sum())
    mun_com_vinc = int(series_df["municipios_com_vinculo"].max())
    cbo_count = int(series_df["ocupacoes_cbo"].max())
else:
    total_vinc = mun_com_vinc = cbo_count = 0

if not municipal_panel.empty:
    pop_total = municipal_panel.groupby("ano")["populacao_usada"].sum().mean()
    taxa_media = (total_vinc / (pop_total * len(selected_years)) * tax_base) if pop_total and len(selected_years) else 0
    mun_total = municipal_panel["cod_municipio"].nunique()
else:
    taxa_media = 0
    mun_total = 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Vínculos", fmt_int(total_vinc))
k2.metric("Municípios com vínculo", fmt_int(mun_com_vinc))
k3.metric("Municípios no filtro", fmt_int(mun_total if mun_total else mun_com_vinc))
k4.metric("CBOs", fmt_int(cbo_count))
k5.metric(f"Taxa média — {tax_label}", fmt_float(taxa_media, 2) if mun_total else "—")


tabs = st.tabs(
    [
        "Painel executivo",
        "Taxas e boxplots",
        "Território",
        "Especialidades",
        "Setor / vínculo",
        "Perfil e desigualdades",
        "Salários",
        "Exportações",
    ]
)


with tabs[0]:
    st.markdown('<div class="ow-section-title">Painel executivo</div>', unsafe_allow_html=True)

    if series_df.empty:
        st.warning("Nenhum dado retornou para os filtros selecionados.")
    else:
        left, right = st.columns([1.3, 1])

        with left:
            fig = px.line(
                series_df,
                x="ano",
                y="vinculos",
                markers=True,
                title="Evolução dos vínculos odontológicos",
                labels={"ano": "Ano", "vinculos": "Vínculos"},
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

        with right:
            fig = px.bar(
                series_df,
                x="ano",
                y="municipios_com_vinculo",
                text="municipios_com_vinculo",
                title="Municípios com vínculos",
                labels={"ano": "Ano", "municipios_com_vinculo": "Municípios"},
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

        if not municipal_panel.empty:
            taxa_ano = (
                municipal_panel.groupby("ano", as_index=False)
                .agg(vinculos=("vinculos", "sum"), populacao=("populacao_usada", "sum"))
            )
            taxa_ano["taxa"] = taxa_ano["vinculos"] / taxa_ano["populacao"] * tax_base

            fig = px.bar(
                taxa_ano,
                x="ano",
                y="taxa",
                text="taxa",
                title=f"Taxa agregada anual — {tax_label}",
                labels={"ano": "Ano", "taxa": tax_label},
            )
            fig.update_xaxes(dtick=1)
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            plot(fig)

        if show_raw_tables:
            show_table(friendly_columns(series_df))
            download_buttons(friendly_columns(series_df), "painel_executivo_serie")


with tabs[1]:
    st.markdown('<div class="ow-section-title">Taxas per capita e distribuição municipal</div>', unsafe_allow_html=True)

    if municipal_panel.empty:
        st.warning("A análise per capita exige a tabela de regiões e/ou populações municipais.")
    else:
        fig = px.box(
            municipal_panel,
            x="ano",
            y="taxa_municipal",
            points="outliers",
            title=f"Distribuição municipal das taxas — {tax_label}",
            labels={"ano": "Ano", "taxa_municipal": tax_label},
        )
        fig.update_xaxes(type="category")
        plot(fig)

        c1, c2 = st.columns([1.1, 1])

        with c1:
            fig = px.box(
                municipal_panel,
                x="sg_uf",
                y="taxa_municipal",
                color="ano",
                points=False,
                title=f"Variação municipal das taxas por UF — {tax_label}",
                labels={"sg_uf": "UF", "taxa_municipal": tax_label},
            )
            plot(fig)

        with c2:
            ultimo = max(selected_years)
            top = municipal_panel[municipal_panel["ano"] == ultimo].sort_values("taxa_municipal", ascending=False).head(max_categories)
            fig = px.bar(
                top.sort_values("taxa_municipal"),
                x="taxa_municipal",
                y="municipio_label",
                orientation="h",
                title=f"Maiores taxas municipais — {ultimo}",
                labels={"taxa_municipal": tax_label, "municipio_label": ""},
            )
            plot(fig)

        resumo = (
            municipal_panel.groupby("ano", as_index=False)
            .agg(
                vinculos=("vinculos", "sum"),
                populacao=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                mediana_taxa=("taxa_municipal", "median"),
                media_taxa=("taxa_municipal", "mean"),
            )
        )
        resumo["taxa_agregada"] = resumo["vinculos"] / resumo["populacao"] * tax_base

        if show_raw_tables:
            show_table(friendly_columns(resumo))
            download_buttons(friendly_columns(resumo), "taxas_resumo_ano", {"resumo": friendly_columns(resumo), "municipios": friendly_columns(municipal_panel)})


with tabs[2]:
    st.markdown('<div class="ow-section-title">Território: regiões e macrorregiões de saúde</div>', unsafe_allow_html=True)

    if municipal_panel.empty:
        st.warning("A visão territorial exige a tabela de regiões.")
    else:
        region = (
            municipal_panel.groupby(["ano", "sg_uf", "regiao_de_saude"], as_index=False)
            .agg(
                vinculos=("vinculos", "sum"),
                populacao=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                mediana_municipal=("taxa_municipal", "median"),
            )
        )
        region["taxa_regional"] = region["vinculos"] / region["populacao"] * tax_base

        macro = (
            municipal_panel.groupby(["ano", "sg_uf", "macrorregiao_de_saude"], as_index=False)
            .agg(
                vinculos=("vinculos", "sum"),
                populacao=("populacao_usada", "sum"),
                municipios=("cod_municipio", "nunique"),
                mediana_municipal=("taxa_municipal", "median"),
            )
        )
        macro["taxa_macro"] = macro["vinculos"] / macro["populacao"] * tax_base

        c1, c2 = st.columns(2)

        with c1:
            fig = px.box(
                region,
                x="ano",
                y="taxa_regional",
                points="all",
                title=f"Distribuição entre regiões de saúde — {tax_label}",
                labels={"taxa_regional": tax_label, "ano": "Ano"},
            )
            fig.update_xaxes(type="category")
            plot(fig)

        with c2:
            fig = px.box(
                macro,
                x="ano",
                y="taxa_macro",
                points="all",
                title=f"Distribuição entre macrorregiões — {tax_label}",
                labels={"taxa_macro": tax_label, "ano": "Ano"},
            )
            fig.update_xaxes(type="category")
            plot(fig)

        ultimo = max(selected_years)
        top_region = region[region["ano"] == ultimo].sort_values("taxa_regional", ascending=False).head(max_categories)
        fig = px.bar(
            top_region.sort_values("taxa_regional"),
            x="taxa_regional",
            y="regiao_de_saude",
            color="sg_uf",
            orientation="h",
            title=f"Regiões de saúde com maiores taxas — {ultimo}",
            labels={"taxa_regional": tax_label, "regiao_de_saude": ""},
        )
        plot(fig)

        if show_raw_tables:
            st.markdown("#### Regiões de saúde")
            show_table(friendly_columns(region), height=360)
            st.markdown("#### Macrorregiões de saúde")
            show_table(friendly_columns(macro), height=360)
            download_buttons(
                friendly_columns(region),
                "territorio_regioes_macros",
                {"regioes": friendly_columns(region), "macrorregioes": friendly_columns(macro)},
            )


with tabs[3]:
    st.markdown('<div class="ow-section-title">Especialidades odontológicas / CBO</div>', unsafe_allow_html=True)

    cbo_sql = sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') AS cbo,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
        FROM {TABLE}
        WHERE {where_sql}
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """)

    cbo_summary = cbo_sql.merge(cbo_map, on="cbo", how="left")
    cbo_summary["cbo_nome"] = cbo_summary["cbo_nome"].fillna("CBO " + cbo_summary["cbo"])
    cbo_summary["grupo_ocupacional"] = cbo_summary["grupo_ocupacional"].fillna("Outras ocupações odontológicas")
    cbo_summary["familia_especialidade"] = cbo_summary["familia_especialidade"].fillna("Não classificada")
    cbo_summary["cbo_label"] = cbo_summary["cbo_nome"] + " — " + cbo_summary["cbo"]

    top = cbo_summary.groupby("cbo_label")["vinculos"].sum().sort_values(ascending=False).head(max_categories).index
    plot_df = cbo_summary[cbo_summary["cbo_label"].isin(top)].copy()

    c1, c2 = st.columns([1.05, 1])

    with c1:
        fig = px.bar(
            plot_df,
            x="cbo_label",
            y="vinculos",
            color="ano",
            barmode="group",
            title=f"Top {max_categories} especialidades / CBO",
            labels={"cbo_label": "", "vinculos": "Vínculos", "ano": "Ano"},
        )
        plot(fig)

    with c2:
        fam = (
            cbo_summary.groupby(["ano", "familia_especialidade"], as_index=False)["vinculos"].sum()
        )
        top_fam = fam.groupby("familia_especialidade")["vinculos"].sum().sort_values(ascending=False).head(max_categories).index
        fam = fam[fam["familia_especialidade"].isin(top_fam)]
        fig = px.line(
            fam,
            x="ano",
            y="vinculos",
            color="familia_especialidade",
            markers=True,
            title="Evolução por família de especialidade",
            labels={"ano": "Ano", "vinculos": "Vínculos", "familia_especialidade": "Família"},
        )
        fig.update_xaxes(dtick=1)
        plot(fig)

    if not municipal_panel.empty:
        # taxa por CBO em municípios: consulta específica por município-CBO-ano
        cbo_mun = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                {mun_key_expr(municipio_col)} AS cod_municipio,
                REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') AS cbo,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE {where_sql}
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """)
        if not cbo_mun.empty:
            terr_cols = municipal_panel[["ano", "cod_municipio", "populacao_usada"]].drop_duplicates()
            cbo_mun = cbo_mun.merge(terr_cols, on=["ano", "cod_municipio"], how="left")
            cbo_mun["taxa"] = cbo_mun.apply(
                lambda r: (r["vinculos"] / r["populacao_usada"] * tax_base) if pd.notna(r["populacao_usada"]) and r["populacao_usada"] > 0 else 0,
                axis=1,
            )
            cbo_mun = cbo_mun.merge(cbo_map, on="cbo", how="left")
            cbo_mun["cbo_nome"] = cbo_mun["cbo_nome"].fillna("CBO " + cbo_mun["cbo"])
            top_cbo = cbo_mun.groupby("cbo_nome")["vinculos"].sum().sort_values(ascending=False).head(12).index
            box = cbo_mun[cbo_mun["cbo_nome"].isin(top_cbo)].copy()

            fig = px.box(
                box,
                x="cbo_nome",
                y="taxa",
                color="ano",
                points=False,
                title=f"Variação municipal das taxas por especialidade — {tax_label}",
                labels={"cbo_nome": "", "taxa": tax_label, "ano": "Ano"},
            )
            plot(fig)

    if show_raw_tables:
        show_table(friendly_columns(cbo_summary), height=420)
        download_buttons(friendly_columns(cbo_summary), "especialidades_cbo")


with tabs[4]:
    st.markdown('<div class="ow-section-title">Setor, tipo de vínculo e natureza jurídica</div>', unsafe_allow_html=True)

    dimensions = []
    if tipo_vinculo_col:
        dimensions.append(("Tipo de vínculo", tipo_vinculo_col, decode_tipo_vinculo))
    if natureza_col:
        dimensions.append(("Grupo da natureza jurídica", natureza_col, decode_natureza_grupo))
        dimensions.append(("Natureza jurídica detalhada", natureza_col, decode_natureza_detalhe))
    if cnae_col:
        dimensions.append(("CNAE / setor econômico", cnae_col, decode_cnae))

    if not dimensions:
        st.warning("Não foram detectadas colunas de tipo de vínculo, natureza jurídica ou CNAE.")
    else:
        dim_names = [d[0] for d in dimensions]
        selected_dim = st.selectbox("Dimensão", dim_names)
        dim_name, dim_col, decoder = dimensions[dim_names.index(selected_dim)]

        raw = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                CAST({q(dim_col)} AS VARCHAR) AS categoria_original,
                COUNT(*) AS vinculos,
                COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
            FROM {TABLE}
            WHERE {where_sql}
              AND {q(dim_col)} IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
        """)

        if raw.empty:
            st.warning("Sem dados para a dimensão selecionada.")
        else:
            raw["categoria"] = raw["categoria_original"].apply(decoder)
            setor = raw.groupby(["ano", "categoria"], as_index=False).agg(vinculos=("vinculos", "sum"), municipios=("municipios", "max"))

            top = setor.groupby("categoria")["vinculos"].sum().sort_values(ascending=False).head(max_categories).index
            plot_df = setor.copy()
            plot_df["categoria_plot"] = plot_df["categoria"].where(plot_df["categoria"].isin(top), "Outros")
            plot_df = plot_df.groupby(["ano", "categoria_plot"], as_index=False)["vinculos"].sum()

            last = max(selected_years)
            last_df = plot_df[plot_df["ano"] == last].sort_values("vinculos", ascending=True)

            fig = px.bar(
                last_df,
                x="vinculos",
                y="categoria_plot",
                orientation="h",
                text="vinculos",
                title=f"{dim_name} — distribuição em {last}",
                labels={"vinculos": "Vínculos", "categoria_plot": ""},
            )
            fig.update_layout(height=max(480, 30 * len(last_df) + 180), showlegend=False)
            plot(fig)

            fig = px.area(
                plot_df,
                x="ano",
                y="vinculos",
                color="categoria_plot",
                groupnorm="percent",
                title=f"Composição percentual — {dim_name}",
                labels={"ano": "Ano", "vinculos": "% dos vínculos", "categoria_plot": ""},
            )
            fig.update_xaxes(dtick=1)
            plot(fig)

            if show_raw_tables:
                setor_out = setor.rename(columns={"ano": "Ano", "categoria": "Categoria", "vinculos": "Vínculos", "municipios": "Municípios"})
                show_table(setor_out, height=420)
                download_buttons(setor_out, f"setor_vinculo_{selected_dim.lower().replace(' ', '_')}")


with tabs[5]:
    st.markdown('<div class="ow-section-title">Perfil e desigualdades</div>', unsafe_allow_html=True)

    dims = []
    if sexo_col:
        dims.append(("Sexo", sexo_col, decode_sex))
    if raca_col:
        dims.append(("Raça/cor", raca_col, decode_race))
    if uf_col_db:
        dims.append(("UF registrada na RAIS", uf_col_db, lambda x: str(x).strip() if str(x).strip() else "Não informado"))

    if not dims:
        st.warning("Nenhuma coluna de perfil detectada.")
    else:
        dim_labels = [d[0] for d in dims]
        selected_dim = st.selectbox("Dimensão de perfil", dim_labels)
        _, dim_col, decoder = dims[dim_labels.index(selected_dim)]

        df = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                CAST({q(dim_col)} AS VARCHAR) AS grupo_original,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE {where_sql}
              AND {q(dim_col)} IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
        """)
        df["grupo"] = df["grupo_original"].apply(decoder)
        agg = df.groupby(["ano", "grupo"], as_index=False)["vinculos"].sum()

        fig = px.bar(
            agg,
            x="grupo",
            y="vinculos",
            color="ano",
            barmode="group",
            title=f"Distribuição por {selected_dim}",
            labels={"grupo": selected_dim, "vinculos": "Vínculos", "ano": "Ano"},
        )
        plot(fig)

        fig = px.area(
            agg,
            x="ano",
            y="vinculos",
            color="grupo",
            groupnorm="percent",
            title=f"Composição percentual por {selected_dim}",
            labels={"ano": "Ano", "vinculos": "% dos vínculos", "grupo": selected_dim},
        )
        fig.update_xaxes(dtick=1)
        plot(fig)

        if show_raw_tables:
            out = agg.rename(columns={"ano": "Ano", "grupo": selected_dim, "vinculos": "Vínculos"})
            show_table(out)
            download_buttons(out, f"perfil_{selected_dim.lower().replace('/', '_')}")


with tabs[6]:
    st.markdown('<div class="ow-section-title">Panorama salarial</div>', unsafe_allow_html=True)

    if not salario_cols:
        st.warning("Nenhuma coluna salarial foi detectada.")
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
        best_col = diag.groupby("coluna")["validos"].sum().sort_values(ascending=False).index[0]
        expr = numeric_expr(best_col)

        st.markdown(
            f'<div class="ow-note">Coluna salarial usada nos gráficos: <b>{best_col}</b>. '
            'A tabela de diagnóstico mostra a completude das demais alternativas.</div>',
            unsafe_allow_html=True,
        )

        sal = sql_df(f"""
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

        plot_df = sal.dropna(subset=["remuneracao_media"])
        if not plot_df.empty:
            fig = px.line(
                plot_df,
                x="ano",
                y=["remuneracao_media", "remuneracao_mediana", "p25", "p75"],
                markers=True,
                title="Remuneração — média, mediana e quartis",
                labels={"ano": "Ano", "value": "Remuneração", "variable": "Indicador"},
            )
            fig.update_xaxes(dtick=1)
            plot(fig)
        else:
            st.warning("Não há valores salariais numéricos positivos suficientes para gráfico.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Diagnóstico das colunas salariais")
            show_table(friendly_columns(diag), height=320)
        with c2:
            st.markdown("#### Resumo anual")
            show_table(friendly_columns(sal), height=320)

        download_buttons(friendly_columns(sal), "panorama_salarial", {"salarios": friendly_columns(sal), "diagnostico": friendly_columns(diag)})


with tabs[7]:
    st.markdown('<div class="ow-section-title">Exportações e auditoria</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ow-note">As tabelas abaixo são úteis para auditar filtros, anos, populações usadas e códigos originais.</div>',
        unsafe_allow_html=True,
    )

    export_tables = {"serie_temporal": friendly_columns(series_df)}

    if not municipal_panel.empty:
        export_tables["municipios_taxas"] = friendly_columns(municipal_panel)
    export_tables["cbo_filtrados"] = friendly_columns(cbo_filtered)
    export_tables["colunas_banco"] = pd.DataFrame({"Coluna original": cols})

    show_table(export_tables["serie_temporal"])
    download_buttons(export_tables["serie_temporal"], "exportacao_geral_v5", export_tables)

    with st.expander("Colunas originais do banco", expanded=False):
        show_table(export_tables["colunas_banco"])

    with st.expander("CBOs disponíveis após os filtros", expanded=False):
        show_table(export_tables["cbo_filtrados"], height=420)


st.markdown(
    '<div class="ow-footer">OdontoWorkforce Brasil V5 — painel experimental para análise de força de trabalho odontológica com RAIS, regiões de saúde e populações IBGE/TCU.</div>',
    unsafe_allow_html=True,
)
