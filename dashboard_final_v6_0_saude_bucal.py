
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any
import json
import re

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
TABLE = "odontologia_saude_bucal_vinculos"

BASE_TABLE = "odontologia_vinculos"


def ensure_saude_bucal_view():
    """
    Cria/atualiza uma view estrita de Saúde Bucal a partir da tabela geral.
    O painel principal usa apenas CD, TSB, ASB, TPD e APD.
    """
    if not DB_PATH.exists():
        return

    con = duckdb.connect(str(DB_PATH))
    try:
        tables = con.execute("SHOW TABLES").fetchdf()["name"].astype(str).tolist()
        if BASE_TABLE not in tables:
            return

        con.execute(f"""
            CREATE OR REPLACE VIEW {TABLE} AS
            SELECT *
            FROM {BASE_TABLE}
            WHERE
                REGEXP_REPLACE(CAST(cbo AS VARCHAR), '[^0-9]', '', 'g') LIKE '2232%'
                OR REGEXP_REPLACE(CAST(cbo AS VARCHAR), '[^0-9]', '', 'g') IN (
                    '322405',
                    '322410',
                    '322415',
                    '322420',
                    '322425',
                    '322430'
                )
        """)
    finally:
        con.close()


ensure_saude_bucal_view()


REFERENCE_DIRS = [
    APP_DIR / "reference",
    ROOT_DIR / "reference",
    APP_DIR,
]

ASSET_DIRS = [
    APP_DIR / "assets",
    ROOT_DIR / "assets",
    APP_DIR,
    ROOT_DIR,
]

TERRITORY_NAMES = ["tabela_regioes(1).csv", "tabela_regioes.csv"]
POP_NAMES = ["populacao_tcu_municipios.csv", "populacao_municipios.csv"]
CBO_MAP_NAMES = ["cbo_odontologia_mapa.csv", "cbo_mapa.csv"]
UF_GEOJSON_NAMES = ["br_ufs.geojson", "br_uf.geojson", "ufs.geojson", "uf.geojson"]
MUNICIPIO_GEOJSON_NAMES = ["br_municipios.geojson", "municipios.geojson", "br_municipios.json"]

st.set_page_config(
    page_title="OdontoWorkforce Brasil — V6.0 Saúde Bucal",
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


def find_asset_file(names: list[str]) -> Path | None:
    for refdir in ASSET_DIRS:
        for name in names:
            p = refdir / name
            if p.exists():
                return p
    return None


def guess_geojson_property(props: dict[str, Any], kind: str) -> str | None:
    keys = list(props.keys())
    lower_map = {str(k).lower(): k for k in keys}

    if kind == "uf":
        candidates = [
            "sigla_uf", "sg_uf", "uf", "sigla", "abbr", "codigo_uf", "cd_uf", "id"
        ]
    else:
        candidates = [
            "cod_municipio", "codigo_municipio", "cod_mun", "cd_mun", "cd_geocmu",
            "geocodigo", "geocodig", "id", "codigo", "codarea"
        ]

    for cand in candidates:
        if cand in keys:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    # fallback heurístico
    for k in keys:
        val = props.get(k)
        sval = str(val).strip()
        if kind == "uf" and len(sval) == 2 and sval.isalpha():
            return k
        if kind == "municipio":
            dig = re.sub(r"[^0-9]", "", sval)
            if len(dig) in (6, 7):
                return k
    return None


@st.cache_data(show_spinner=False)
def load_geojson(kind: str) -> tuple[dict[str, Any] | None, str]:
    if kind == "uf":
        path = find_asset_file(UF_GEOJSON_NAMES)
    else:
        path = find_asset_file(MUNICIPIO_GEOJSON_NAMES)

    if path is None:
        return None, ""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, ""

    feats = data.get("features", [])
    if not feats:
        return None, str(path)

    sample_props = feats[0].get("properties", {}) or {}
    prop = guess_geojson_property(sample_props, kind)

    for feat in feats:
        props = feat.setdefault("properties", {})
        raw = props.get(prop) if prop else feat.get("id", "")
        if kind == "uf":
            match = str(raw).strip().upper()
        else:
            match = normalize_municipio_code_py(raw)
        props["__match"] = match

    return data, str(path)


def pick(cols: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def normalize_municipio_code_py(value: Any) -> str:
    """
    Normaliza código municipal para 6 dígitos, compatível com a tabela de regiões.

    Regras:
    - 6 dígitos: mantém.
    - 7 dígitos começando com 0: usa os 6 últimos.
      Ex.: 0310620 -> 310620.
    - 7 dígitos sem zero inicial: usa os 6 primeiros.
      Ex.: 3106200 -> 310620.
    - Mais de 7 dígitos: tenta remover zeros iniciais e aplicar a mesma lógica.
    """
    if pd.isna(value):
        return ""
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return ""

    if len(digits) < 6:
        return digits.zfill(6)

    if len(digits) == 6:
        return digits

    if len(digits) == 7:
        if digits.startswith("0"):
            return digits[-6:]
        return digits[:6]

    stripped = digits.lstrip("0")
    if len(stripped) == 6:
        return stripped
    if len(stripped) == 7:
        if stripped.startswith("0"):
            return stripped[-6:]
        return stripped[:6]
    return digits[:6]


def mun_key_expr(col: str) -> str:
    digits = f"REGEXP_REPLACE(CAST({q(col)} AS VARCHAR), '[^0-9]', '', 'g')"
    stripped = f"REGEXP_REPLACE({digits}, '^0+', '')"
    return f"""
    CASE
        WHEN LENGTH({digits}) < 6 THEN LPAD({digits}, 6, '0')
        WHEN LENGTH({digits}) = 6 THEN {digits}
        WHEN LENGTH({digits}) = 7 AND LEFT({digits}, 1) = '0' THEN RIGHT({digits}, 6)
        WHEN LENGTH({digits}) = 7 THEN SUBSTR({digits}, 1, 6)
        WHEN LENGTH({stripped}) = 6 THEN {stripped}
        WHEN LENGTH({stripped}) = 7 AND LEFT({stripped}, 1) = '0' THEN RIGHT({stripped}, 6)
        WHEN LENGTH({stripped}) = 7 THEN SUBSTR({stripped}, 1, 6)
        ELSE SUBSTR({digits}, 1, 6)
    END
    """


def municipio_candidates_py(value: Any) -> list[str]:
    """
    Gera candidatos possíveis de código municipal de 6 dígitos.
    Usado para compatibilizar formatos heterogêneos da RAIS com a tabela territorial.
    """
    if pd.isna(value):
        return []
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return []

    stripped = digits.lstrip("0")
    candidates = []

    def add(x: str):
        if x and len(x) == 6 and x not in candidates:
            candidates.append(x)

    # Caso já esteja em 6 dígitos.
    if len(digits) == 6:
        add(digits)

    # Caso tenha menos de 6.
    if len(digits) < 6:
        add(digits.zfill(6))

    # Formatos com 7+ dígitos: pode ser IBGE completo, zero + 6 dígitos, ou string com lixo/sufixo.
    if len(digits) >= 6:
        add(digits[:6])
        add(digits[-6:])

    if len(stripped) >= 6:
        add(stripped[:6])
        add(stripped[-6:])

    if len(stripped) < 6 and stripped:
        add(stripped.zfill(6))

    # Acrescenta a regra determinística anterior por último.
    add(normalize_municipio_code_py(value))

    return candidates


def normalize_municipio_code_validated(value: Any, valid_codes: set[str]) -> str:
    """
    Escolhe o primeiro candidato que existe na tabela territorial.
    Se nenhum candidato existir, retorna a normalização determinística.
    """
    candidates = municipio_candidates_py(value)
    for c in candidates:
        if c in valid_codes:
            return c
    return candidates[0] if candidates else ""



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

    df["cod_municipio"] = df["cod_municipio"].apply(normalize_municipio_code_py)
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

    out["cod_municipio"] = out["cod_municipio"].apply(normalize_municipio_code_py)
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
            Painel V6.0 Saúde Bucal — composição ocupacional, densidades, território, vínculos e perfil sociodemográfico.
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
    st.markdown(
        """
        <div class="ow-note">
        Seleção revisada: o painel usa internamente apenas o código CBO. 
        Os nomes completos aparecem somente na tela. Isso evita erros de seleção causados por rótulos compostos.
        </div>
        """,
        unsafe_allow_html=True,
    )

    cbo_counts = base_cbo_counts(ano_col, cbo_col, where_without_cbo)
    cbo_counts["cbo"] = cbo_counts["cbo"].astype(str).str.replace(r"\D", "", regex=True)

    cbo_options = cbo_counts.merge(cbo_map, on="cbo", how="left")
    cbo_options["cbo_nome"] = cbo_options["cbo_nome"].fillna("CBO " + cbo_options["cbo"])
    cbo_options["grupo_ocupacional"] = cbo_options["grupo_ocupacional"].fillna("Outras ocupações presentes no recorte odontológico")
    cbo_options["familia_especialidade"] = cbo_options["familia_especialidade"].fillna("Não classificada")
    if "status_mapeamento" not in cbo_options.columns:
        cbo_options["status_mapeamento"] = "mapeado/sem status"

    cbo_options = cbo_options.sort_values(
        ["grupo_ocupacional", "familia_especialidade", "cbo_nome", "cbo"],
        ascending=[True, True, True, True],
    ).copy()

    all_cbo_codes = cbo_options["cbo"].dropna().astype(str).unique().tolist()

    def cbo_format(code: str) -> str:
        row = cbo_options.loc[cbo_options["cbo"].astype(str) == str(code)]
        if row.empty:
            return str(code)
        r = row.iloc[0]
        return f'{r["cbo"]} — {r["cbo_nome"]}'

    st.caption(f"{len(all_cbo_codes)} CBOs disponíveis depois dos filtros de período/território.")

    cbo_filtered = cbo_options.copy()

    escopo = st.radio(
        "Escopo ocupacional",
        [
            "Todas as ocupações do recorte",
            "Cirurgiões-dentistas",
            "Equipe auxiliar odontológica",
            "Outras / revisar pertinência",
        ],
        index=0,
        help="Este filtro atua sobre o grupo ocupacional do mapa de CBO.",
    )

    if escopo == "Cirurgiões-dentistas":
        cbo_filtered = cbo_filtered[
            cbo_filtered["grupo_ocupacional"].str.contains("Cirurgi", case=False, na=False)
        ].copy()
    elif escopo == "Equipe auxiliar odontológica":
        cbo_filtered = cbo_filtered[
            cbo_filtered["grupo_ocupacional"].str.contains("auxiliar|técnico|tecnico|prótese|protese", case=False, na=False)
        ].copy()
    elif escopo == "Outras / revisar pertinência":
        cbo_filtered = cbo_filtered[
            ~cbo_filtered["grupo_ocupacional"].str.contains("Cirurgi|auxiliar|técnico|tecnico|prótese|protese", case=False, na=False)
        ].copy()

    grupos = sorted(cbo_filtered["grupo_ocupacional"].dropna().unique().tolist())
    selected_grupos = st.multiselect(
        "Grupo ocupacional",
        options=grupos,
        default=[],
        placeholder="Todos os grupos",
        help="Deixe vazio para manter todos os grupos do escopo escolhido.",
    )
    if selected_grupos:
        cbo_filtered = cbo_filtered[cbo_filtered["grupo_ocupacional"].isin(selected_grupos)].copy()

    familias = sorted(cbo_filtered["familia_especialidade"].dropna().unique().tolist())
    selected_familias = st.multiselect(
        "Família de especialidade",
        options=familias,
        default=[],
        placeholder="Todas as famílias",
        help="Deixe vazio para manter todas as famílias.",
    )
    if selected_familias:
        cbo_filtered = cbo_filtered[cbo_filtered["familia_especialidade"].isin(selected_familias)].copy()

    busca_cbo = st.text_input(
        "Buscar especialidade ou CBO",
        placeholder="Ex.: endodontia, prótese, 322405, saúde coletiva...",
    ).strip().lower()

    if busca_cbo:
        cbo_filtered = cbo_filtered[
            cbo_filtered["cbo"].astype(str).str.lower().str.contains(busca_cbo, regex=False)
            | cbo_filtered["cbo_nome"].astype(str).str.lower().str.contains(busca_cbo, regex=False)
            | cbo_filtered["grupo_ocupacional"].astype(str).str.lower().str.contains(busca_cbo, regex=False)
            | cbo_filtered["familia_especialidade"].astype(str).str.lower().str.contains(busca_cbo, regex=False)
            | cbo_filtered["status_mapeamento"].astype(str).str.lower().str.contains(busca_cbo, regex=False)
        ].copy()

    cbo_filtered = cbo_filtered.sort_values("vinculos", ascending=False).copy()
    filtered_codes = cbo_filtered["cbo"].dropna().astype(str).unique().tolist()

    if not filtered_codes:
        st.warning("Nenhum CBO encontrado com os filtros de especialidade atuais.")
        selected_cbos = []
    else:
        modo = st.radio(
            "Como aplicar a seleção de CBO?",
            ["Usar todos os CBOs filtrados", "Usar Top N", "Selecionar manualmente"],
            index=0,
        )

        if modo == "Usar Top N":
            max_top = max(1, len(filtered_codes))
            top_n = st.slider(
                "Número de CBOs mais frequentes",
                min_value=1,
                max_value=min(100, max_top),
                value=min(20, max_top),
                step=1,
            )
            selected_cbos = filtered_codes[:top_n]

        elif modo == "Selecionar manualmente":
            selected_cbos = st.multiselect(
                "CBOs",
                options=filtered_codes,
                default=[],
                format_func=cbo_format,
                placeholder="Selecione um ou mais CBOs",
                help="Internamente o filtro usa apenas o código CBO; o nome é apenas visual.",
            )
            if not selected_cbos:
                st.info("Nenhum CBO manual selecionado. O painel usará todos os CBOs filtrados acima.")
                selected_cbos = filtered_codes
        else:
            selected_cbos = filtered_codes

        selected_preview = cbo_filtered[cbo_filtered["cbo"].astype(str).isin(selected_cbos)].copy()

        st.caption(
            f"Aplicando {len(selected_cbos)} CBOs de {len(all_cbo_codes)} disponíveis no período/território."
        )

        with st.expander("Ver CBOs que serão usados", expanded=False):
            preview_cols = [
                "cbo",
                "cbo_nome",
                "grupo_ocupacional",
                "familia_especialidade",
                "vinculos",
                "anos_com_dado",
                "status_mapeamento",
            ]
            preview_cols = [c for c in preview_cols if c in selected_preview.columns]
            show_table(friendly_columns(selected_preview[preview_cols]), height=320)

    if selected_cbos and len(selected_cbos) < len(all_cbo_codes):
        where_parts.append(
            f"REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') "
            f"IN ({','.join(lit(x) for x in selected_cbos)})"
        )


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
    # Importante: retornamos o código municipal BRUTO da RAIS.
    # A compatibilização com a tabela territorial é feita em Python usando valid_codes.
    return sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            CAST({q(municipio_col)} AS VARCHAR) AS cod_municipio_raw,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g')) AS ocupacoes_cbo
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)


def municipio_code_diagnostics() -> pd.DataFrame:
    digits_expr = f"REGEXP_REPLACE(CAST({q(municipio_col)} AS VARCHAR), '[^0-9]', '', 'g')"
    norm_expr = mun_key_expr(municipio_col)
    diag = sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            LENGTH({digits_expr}) AS tamanho_codigo_municipio,
            COUNT(*) AS vinculos,
            COUNT(DISTINCT CAST({q(municipio_col)} AS VARCHAR)) AS codigos_originais_distintos,
            COUNT(DISTINCT {norm_expr}) AS codigos_normalizados_deterministicos,
            MIN(CAST({q(municipio_col)} AS VARCHAR)) AS exemplo_min,
            MAX(CAST({q(municipio_col)} AS VARCHAR)) AS exemplo_max
        FROM {TABLE}
        WHERE CAST({q(ano_col)} AS INTEGER) BETWEEN {ano_ini} AND {ano_fim}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    if territory is not None:
        valid_codes = set(territory["cod_municipio"].astype(str).tolist())
        sample = sql_df(f"""
            SELECT
                CAST({q(ano_col)} AS INTEGER) AS ano,
                CAST({q(municipio_col)} AS VARCHAR) AS cod_municipio_raw,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE CAST({q(ano_col)} AS INTEGER) BETWEEN {ano_ini} AND {ano_fim}
            GROUP BY 1, 2
        """)
        sample["cod_validado"] = sample["cod_municipio_raw"].apply(
            lambda x: normalize_municipio_code_validated(x, valid_codes)
        )
        sample["validado_encontrado_territorio"] = sample["cod_validado"].isin(valid_codes)
        # Cálculo explícito.
        match = (
            sample[sample["validado_encontrado_territorio"]]
            .groupby("ano", as_index=False)["vinculos"]
            .sum()
            .rename(columns={"vinculos": "vinculos_com_codigo_validado"})
        )
        total = sample.groupby("ano", as_index=False)["vinculos"].sum().rename(columns={"vinculos": "vinculos_total"})
        match = total.merge(match, on="ano", how="left")
        match["vinculos_com_codigo_validado"] = match["vinculos_com_codigo_validado"].fillna(0)
        match["percentual_codigo_validado"] = match["vinculos_com_codigo_validado"] / match["vinculos_total"].replace(0, pd.NA) * 100

        diag = diag.merge(match, on="ano", how="left")

    return diag


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
    valid_codes = set(base_territory["cod_municipio"].astype(str).tolist())

    if "cod_municipio_raw" in counts2.columns:
        counts2["cod_municipio"] = counts2["cod_municipio_raw"].apply(
            lambda x: normalize_municipio_code_validated(x, valid_codes)
        )
    else:
        counts2["cod_municipio"] = counts2["cod_municipio"].apply(
            lambda x: normalize_municipio_code_validated(x, valid_codes)
        )

    # Depois de normalizar, reagrupa porque diferentes formatos podem mapear para o mesmo município.
    counts2 = (
        counts2.groupby(["ano", "cod_municipio"], as_index=False)
        .agg(
            vinculos=("vinculos", "sum"),
            ocupacoes_cbo=("ocupacoes_cbo", "max"),
        )
    )

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



# =============================================================================
# MODELO ANALÍTICO — FORÇA DE TRABALHO EM SAÚDE BUCAL
# =============================================================================

CATEGORIA_SB_ORDEM = ["CD", "TSB", "ASB", "TPD", "APD", "Outras"]
CATEGORIA_SB_NOMES = {
    "CD": "Cirurgiões-dentistas",
    "TSB": "Técnicos em saúde bucal",
    "ASB": "Auxiliares em saúde bucal",
    "TPD": "Técnicos em prótese dentária / protéticos",
    "APD": "Auxiliares de prótese dentária",
    "Outras": "Outras ocupações do recorte",
}


def categoria_saude_bucal(cbo_value: Any) -> str:
    """
    Classifica os CBOs no modelo analítico de Saúde Bucal:
    CD, TSB, ASB, TPD, APD e Outras ocupações do recorte.
    """
    c = re.sub(r"[^0-9]", "", str(cbo_value))
    if c.startswith("2232"):
        return "CD"
    if c == "322405":
        return "TSB"
    if c in {"322415", "322430"}:
        return "ASB"
    if c in {"322410", "322425"}:
        return "TPD"
    if c == "322420":
        return "APD"
    return "Outras"


@st.cache_data(show_spinner=True)
def get_cbo_municipal_counts_for_boletim(where_sql_: str) -> pd.DataFrame:
    return sql_df(f"""
        SELECT
            CAST({q(ano_col)} AS INTEGER) AS ano,
            CAST({q(municipio_col)} AS VARCHAR) AS cod_municipio_raw,
            REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') AS cbo,
            COUNT(*) AS vinculos
        FROM {TABLE}
        WHERE {where_sql_}
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
    """)


def build_boletim_panel() -> pd.DataFrame:
    if territory_filtered is None or territory_filtered.empty or municipal_panel.empty:
        return pd.DataFrame()

    raw = get_cbo_municipal_counts_for_boletim(where_sql)
    if raw.empty:
        return pd.DataFrame()

    valid_codes = set(territory_filtered["cod_municipio"].astype(str).tolist())
    raw["cod_municipio"] = raw["cod_municipio_raw"].apply(
        lambda x: normalize_municipio_code_validated(x, valid_codes)
    )
    raw["categoria_sb"] = raw["cbo"].apply(categoria_saude_bucal)

    raw = (
        raw.groupby(["ano", "cod_municipio", "categoria_sb"], as_index=False)["vinculos"]
        .sum()
    )

    terr_cols = [
        "ano",
        "cod_municipio",
        "municipio_label",
        "sg_uf",
        "uf",
        "regiao_de_saude",
        "macrorregiao_de_saude",
        "populacao_usada",
        "tipo_populacao",
    ]
    terr_cols = [c for c in terr_cols if c in municipal_panel.columns]
    panel = raw.merge(
        municipal_panel[terr_cols].drop_duplicates(["ano", "cod_municipio"]),
        on=["ano", "cod_municipio"],
        how="left",
    )
    panel["categoria_nome"] = panel["categoria_sb"].map(CATEGORIA_SB_NOMES).fillna(panel["categoria_sb"])
    return panel


def add_ratio_columns(pivot: pd.DataFrame) -> pd.DataFrame:
    out = pivot.copy()
    for c in CATEGORIA_SB_ORDEM:
        if c not in out.columns:
            out[c] = 0

    out["CD/TSB"] = out.apply(lambda r: r["CD"] / r["TSB"] if r["TSB"] > 0 else pd.NA, axis=1)
    out["CD/ASB"] = out.apply(lambda r: r["CD"] / r["ASB"] if r["ASB"] > 0 else pd.NA, axis=1)
    out["Apoio clínico/CD"] = out.apply(
        lambda r: (r["TSB"] + r["ASB"]) / r["CD"] if r["CD"] > 0 else pd.NA,
        axis=1,
    )
    out["Apoio total/CD"] = out.apply(
        lambda r: (r["TSB"] + r["ASB"] + r["TPD"] + r["APD"]) / r["CD"] if r["CD"] > 0 else pd.NA,
        axis=1,
    )
    return out

boletim_panel = build_boletim_panel()

tabs = st.tabs(
    [
        "Síntese da força de trabalho",
        "Densidades e boxplots",
        "Território",
        "Ocupações odontológicas",
        "Setor / vínculo",
        "Perfil sociodemográfico",
        "Salários",
        "Exportações",
    ]
)


with tabs[0]:
    st.markdown('<div class="ow-section-title">Síntese da força de trabalho em Saúde Bucal</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ow-note">'
        'Esta página apresenta a composição da força de trabalho em Saúde Bucal, densidades por 10 mil habitantes, '
        'distribuição territorial e razões entre cirurgiões-dentistas e ocupações de apoio. '
        'O painel utiliza um recorte estrito de ocupações de Saúde Bucal: CD, TSB, ASB, TPD e APD.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Fonte do modelo analítico", expanded=False):
        st.markdown(
            "O modelo analítico utiliza as categorias CD, TSB, ASB, TPD e APD, "
            "densidades por 10 mil habitantes e razões CD/TSB e CD/ASB como eixos de leitura da composição "
            "e distribuição territorial da força de trabalho em Saúde Bucal."
        )

    if series_df.empty:
        st.warning("Nenhum dado retornou para os filtros selecionados.")
    elif boletim_panel.empty:
        st.warning("A síntese por categoria ocupacional exige tabela territorial e população municipal.")
    else:
        ano_ref = max(selected_years)

        cat_year = (
            boletim_panel.groupby(["ano", "categoria_sb", "categoria_nome"], as_index=False)
            .agg(vinculos=("vinculos", "sum"))
        )
        total_year = cat_year.groupby("ano", as_index=False)["vinculos"].sum().rename(columns={"vinculos": "total_ano"})
        cat_year = cat_year.merge(total_year, on="ano", how="left")
        cat_year["percentual"] = cat_year["vinculos"] / cat_year["total_ano"].replace(0, pd.NA) * 100
        cat_year["categoria_sb"] = pd.Categorical(cat_year["categoria_sb"], categories=CATEGORIA_SB_ORDEM, ordered=True)
        cat_year = cat_year.sort_values(["ano", "categoria_sb"])

        cat_ref = cat_year[cat_year["ano"] == ano_ref].copy()

        pivot_br = (
            cat_year.pivot_table(
                index="ano",
                columns="categoria_sb",
                values="vinculos",
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
            .reset_index()
        )
        pivot_br = add_ratio_columns(pivot_br)
        pivot_ref_df = pivot_br[pivot_br["ano"] == ano_ref]
        pivot_ref = pivot_ref_df.iloc[0] if not pivot_ref_df.empty else None

        cd_ref = float(pivot_ref.get("CD", 0)) if pivot_ref is not None else 0
        tsb_ref = float(pivot_ref.get("TSB", 0)) if pivot_ref is not None else 0
        asb_ref = float(pivot_ref.get("ASB", 0)) if pivot_ref is not None else 0
        apoio_clinico = tsb_ref + asb_ref

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Ano de referência", str(ano_ref))
        k2.metric("CD", fmt_int(cd_ref))
        k3.metric("TSB + ASB", fmt_int(apoio_clinico))
        k4.metric("CD/TSB", fmt_float(pivot_ref.get("CD/TSB"), 2) if pivot_ref is not None and pd.notna(pivot_ref.get("CD/TSB")) else "—")
        k5.metric("CD/ASB", fmt_float(pivot_ref.get("CD/ASB"), 2) if pivot_ref is not None and pd.notna(pivot_ref.get("CD/ASB")) else "—")

        c1, c2 = st.columns([1.05, 1])

        with c1:
            fig = px.bar(
                cat_ref.sort_values("categoria_sb"),
                x="categoria_nome",
                y="vinculos",
                text="vinculos",
                title=f"Composição da força de trabalho em Saúde Bucal — {ano_ref}",
                labels={"categoria_nome": "", "vinculos": "Vínculos RAIS"},
            )
            fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
            fig.update_layout(showlegend=False, height=500)
            plot(fig)

        with c2:
            fig = px.pie(
                cat_ref,
                names="categoria_nome",
                values="vinculos",
                hole=0.48,
                title=f"Participação percentual por categoria — {ano_ref}",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(height=500, showlegend=False)
            plot(fig)

        st.markdown("### Evolução da composição ocupacional")

        fig = px.area(
            cat_year,
            x="ano",
            y="percentual",
            color="categoria_nome",
            title="Composição percentual da força de trabalho por categoria",
            labels={"ano": "Ano", "percentual": "% dos vínculos", "categoria_nome": "Categoria"},
        )
        fig.update_xaxes(dtick=1)
        plot(fig)

        # Densidade por UF e categoria.
        uf_pop = (
            municipal_panel.groupby(["ano", "sg_uf"], as_index=False)
            .agg(populacao=("populacao_usada", "sum"))
        )
        uf_cat = (
            boletim_panel.groupby(["ano", "sg_uf", "categoria_sb", "categoria_nome"], as_index=False)
            .agg(vinculos=("vinculos", "sum"))
            .merge(uf_pop, on=["ano", "sg_uf"], how="left")
        )
        uf_cat["taxa_10000"] = uf_cat["vinculos"] / uf_cat["populacao"].replace(0, pd.NA) * 10000

        uf_ref = uf_cat[uf_cat["ano"] == ano_ref].copy()
        uf_ref["categoria_sb"] = pd.Categorical(uf_ref["categoria_sb"], categories=CATEGORIA_SB_ORDEM, ordered=True)

        st.markdown("### Densidade por Unidade Federativa e categoria")

        categoria_densidade = st.selectbox(
            "Categoria para densidade por UF",
            ["CD", "TSB", "ASB", "TPD", "APD", "Outras"],
            format_func=lambda x: CATEGORIA_SB_NOMES.get(x, x),
            index=0,
        )

        dens = (
            uf_ref[uf_ref["categoria_sb"].astype(str) == categoria_densidade]
            .sort_values("taxa_10000", ascending=True)
            .copy()
        )
        fig = px.bar(
            dens,
            x="taxa_10000",
            y="sg_uf",
            orientation="h",
            text="taxa_10000",
            title=f"Densidade de {CATEGORIA_SB_NOMES.get(categoria_densidade)} por UF — vínculos por 10 mil habitantes, {ano_ref}",
            labels={"taxa_10000": "Vínculos por 10 mil hab.", "sg_uf": "UF"},
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(height=max(520, 24 * len(dens) + 180), showlegend=False)
        plot(fig)

        # Razões CD/TSB e CD/ASB.
        uf_pivot = (
            boletim_panel[boletim_panel["ano"] == ano_ref]
            .groupby(["sg_uf", "categoria_sb"], as_index=False)["vinculos"]
            .sum()
            .pivot_table(index="sg_uf", columns="categoria_sb", values="vinculos", fill_value=0, observed=False)
            .reset_index()
        )
        uf_ratios = add_ratio_columns(uf_pivot)

        st.markdown("### Razões entre CD e ocupações de apoio")

        r1, r2 = st.columns(2)

        with r1:
            df_ratio = uf_ratios.dropna(subset=["CD/TSB"]).sort_values("CD/TSB", ascending=True)
            fig = px.bar(
                df_ratio,
                x="CD/TSB",
                y="sg_uf",
                orientation="h",
                text="CD/TSB",
                title=f"Cirurgiões-dentistas por TSB — {ano_ref}",
                labels={"CD/TSB": "CD por TSB", "sg_uf": "UF"},
            )
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig.update_layout(height=max(520, 24 * len(df_ratio) + 180), showlegend=False)
            plot(fig)

        with r2:
            df_ratio = uf_ratios.dropna(subset=["CD/ASB"]).sort_values("CD/ASB", ascending=True)
            fig = px.bar(
                df_ratio,
                x="CD/ASB",
                y="sg_uf",
                orientation="h",
                text="CD/ASB",
                title=f"Cirurgiões-dentistas por ASB — {ano_ref}",
                labels={"CD/ASB": "CD por ASB", "sg_uf": "UF"},
            )
            fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig.update_layout(height=max(520, 24 * len(df_ratio) + 180), showlegend=False)
            plot(fig)

        st.markdown("### Tabela-súmula por categoria ocupacional")

        resumo = (
            uf_cat[uf_cat["ano"] == ano_ref]
            .pivot_table(
                index="sg_uf",
                columns="categoria_sb",
                values=["vinculos", "taxa_10000"],
                aggfunc="sum",
                fill_value=0,
                observed=False,
            )
        )
        resumo.columns = [f"{a}_{b}" for a, b in resumo.columns]
        resumo = resumo.reset_index()
        resumo_for_ratio = resumo.rename(
            columns={
                "vinculos_CD": "CD",
                "vinculos_TSB": "TSB",
                "vinculos_ASB": "ASB",
                "vinculos_TPD": "TPD",
                "vinculos_APD": "APD",
                "vinculos_Outras": "Outras",
            }
        )
        resumo_for_ratio = add_ratio_columns(resumo_for_ratio)

        keep_cols = ["sg_uf", "CD", "TSB", "ASB", "TPD", "APD", "Outras", "CD/TSB", "CD/ASB", "Apoio clínico/CD"]
        taxa_cols = [c for c in resumo_for_ratio.columns if c.startswith("taxa_10000_")]
        resumo_out = resumo_for_ratio[[c for c in keep_cols if c in resumo_for_ratio.columns] + taxa_cols].copy()

        rename_taxas = {
            "taxa_10000_CD": "Taxa CD/10 mil",
            "taxa_10000_TSB": "Taxa TSB/10 mil",
            "taxa_10000_ASB": "Taxa ASB/10 mil",
            "taxa_10000_TPD": "Taxa TPD/10 mil",
            "taxa_10000_APD": "Taxa APD/10 mil",
            "taxa_10000_Outras": "Taxa Outras/10 mil",
            "sg_uf": "UF",
        }
        resumo_out = resumo_out.rename(columns=rename_taxas)

        show_table(resumo_out, height=420)
        download_buttons(
            resumo_out,
            "sintese_saude_bucal_rais",
            {
                "sintese_uf": resumo_out,
                "composicao_ano": friendly_columns(cat_year),
                "densidade_uf_categoria": friendly_columns(uf_cat),
                "razoes_uf": friendly_columns(uf_ratios),
            },
        )



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
    st.markdown('<div class="ow-section-title">Território: distribuição, dispersão e mapas</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ow-note">'
        'A aba Território foi reorganizada para facilitar a leitura da distribuição territorial. '
        'Os gráficos de distribuição agora podem ser desenhados como violino suave com caixa interna, '
        'reduzindo a confusão visual dos boxplots tradicionais. A aba também inclui mapas coropléticos das '
        'taxas per capita e da distribuição espacial dos vínculos.'
        '</div>',
        unsafe_allow_html=True,
    )

    if municipal_panel.empty or boletim_panel.empty:
        st.warning("A visão territorial exige tabela de regiões, população municipal e dados por categoria ocupacional.")
    else:
        categoria_options = ["Total Saúde Bucal", "CD", "TSB", "ASB", "TPD", "APD", "Outras"]

        csel1, csel2, csel3, csel4 = st.columns([1.15, 1.1, 0.9, 0.85])

        with csel1:
            nivel_territorial = st.selectbox(
                "Nível territorial",
                ["UF", "Macrorregião de saúde", "Região de saúde", "Município"],
                index=1,
            )

        with csel2:
            categoria_territorio = st.selectbox(
                "Categoria ocupacional",
                categoria_options,
                index=0,
                format_func=lambda x: CATEGORIA_SB_NOMES.get(x, x),
            )

        with csel3:
            anos_territorio = sorted(municipal_panel["ano"].dropna().astype(int).unique().tolist())
            ano_territorio = st.selectbox(
                "Ano de destaque",
                anos_territorio,
                index=len(anos_territorio) - 1,
            )

        with csel4:
            limite_ranking = st.slider("Itens no ranking", 10, 80, 30, step=5)

        def build_territory_summary(level: str, categoria: str) -> pd.DataFrame:
            if level == "UF":
                keys = ["ano", "sg_uf"]
                pop = municipal_panel.groupby(keys, as_index=False).agg(populacao=("populacao_usada", "sum"))
                pop["territorio"] = pop["sg_uf"]
            elif level == "Macrorregião de saúde":
                keys = ["ano", "sg_uf", "macrorregiao_de_saude"]
                pop = municipal_panel.groupby(keys, as_index=False).agg(populacao=("populacao_usada", "sum"))
                pop["territorio"] = pop["sg_uf"].astype(str) + " — " + pop["macrorregiao_de_saude"].astype(str)
            elif level == "Região de saúde":
                keys = ["ano", "sg_uf", "regiao_de_saude"]
                pop = municipal_panel.groupby(keys, as_index=False).agg(populacao=("populacao_usada", "sum"))
                pop["territorio"] = pop["sg_uf"].astype(str) + " — " + pop["regiao_de_saude"].astype(str)
            else:
                keys = ["ano", "cod_municipio", "municipio_label", "sg_uf"]
                pop = municipal_panel.groupby(keys, as_index=False).agg(populacao=("populacao_usada", "max"))
                pop["territorio"] = pop["municipio_label"].astype(str)

            if categoria == "Total Saúde Bucal":
                work = boletim_panel.groupby(keys, as_index=False).agg(vinculos=("vinculos", "sum"))
            else:
                work = (
                    boletim_panel[boletim_panel["categoria_sb"] == categoria]
                    .groupby(keys, as_index=False)
                    .agg(vinculos=("vinculos", "sum"))
                )

            out = pop.merge(work, on=keys, how="left")
            out["vinculos"] = out["vinculos"].fillna(0)
            out["taxa_10000"] = out["vinculos"] / out["populacao"].replace(0, pd.NA) * 10000
            out["nivel_territorial"] = level
            out["categoria"] = categoria
            return out

        terr_df = build_territory_summary(nivel_territorial, categoria_territorio)

        if terr_df.empty:
            st.warning("Sem dados territoriais para os filtros atuais.")
        else:
            ref = terr_df[terr_df["ano"] == ano_territorio].copy()

            taxa_valid = ref["taxa_10000"].dropna()
            if taxa_valid.empty:
                mediana = p25 = p75 = p90 = p10 = pd.NA
                razao_p90_p10 = pd.NA
            else:
                mediana = taxa_valid.median()
                p25 = taxa_valid.quantile(0.25)
                p75 = taxa_valid.quantile(0.75)
                p90 = taxa_valid.quantile(0.90)
                p10 = taxa_valid.quantile(0.10)
                razao_p90_p10 = p90 / p10 if pd.notna(p10) and p10 > 0 else pd.NA

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Territórios", fmt_int(ref["territorio"].nunique()))
            m2.metric("Mediana / 10 mil", fmt_float(mediana, 2) if pd.notna(mediana) else "—")
            m3.metric("P25–P75", f"{fmt_float(p25, 2)}–{fmt_float(p75, 2)}" if pd.notna(p25) and pd.notna(p75) else "—")
            m4.metric("P90/P10", fmt_float(razao_p90_p10, 2) if pd.notna(razao_p90_p10) else "—")
            m5.metric("Vínculos", fmt_int(ref["vinculos"].sum()))

            st.markdown("### Distribuição territorial por ano")

            b1, b2, b3, b4 = st.columns([1.25, 1.0, 1.0, 1.0])

            with b1:
                estilo_distrib = st.selectbox(
                    "Desenho da distribuição",
                    ["Violino suave + caixa", "Box plot clássico"],
                    index=0,
                    help="O violino mostra a densidade da distribuição e inclui uma caixa interna com quartis e mediana.",
                )

            with b2:
                mostrar_pontos = st.toggle(
                    "Mostrar pontos",
                    value=False,
                    help="Ligue para visualizar cada território individualmente.",
                )

            with b3:
                escala_box = st.selectbox(
                    "Escala",
                    ["Normal", "Zoom até P95", "Zoom até P99", "Logarítmica"],
                    index=1,
                )

            with b4:
                suavizar_cauda = st.toggle(
                    "Ocultar extremos altos",
                    value=False,
                    help="Aplica um recorte visual até o percentil 99, útil quando poucos extremos dominam a escala.",
                )

            plot_box = terr_df.copy()
            ymax = None
            if escala_box == "Zoom até P95":
                ymax = plot_box["taxa_10000"].quantile(0.95)
            elif escala_box == "Zoom até P99":
                ymax = plot_box["taxa_10000"].quantile(0.99)
            if suavizar_cauda:
                ymax_aux = plot_box["taxa_10000"].quantile(0.99)
                ymax = min(ymax, ymax_aux) if ymax is not None else ymax_aux

            points_mode = "all" if mostrar_pontos else False

            if estilo_distrib == "Violino suave + caixa":
                fig = px.violin(
                    plot_box,
                    x="ano",
                    y="taxa_10000",
                    box=True,
                    points=points_mode,
                    hover_data={
                        "territorio": True,
                        "vinculos": ":,.0f",
                        "populacao": ":,.0f",
                        "taxa_10000": ":.2f",
                        "ano": True,
                    },
                    title=(
                        f"Distribuição territorial — {CATEGORIA_SB_NOMES.get(categoria_territorio, categoria_territorio)} "
                        f"em {nivel_territorial.lower()}"
                    ),
                    labels={
                        "ano": "Ano",
                        "taxa_10000": "Vínculos por 10 mil habitantes",
                    },
                )
                fig.update_traces(meanline_visible=True, jitter=0.04)
            else:
                fig = px.box(
                    plot_box,
                    x="ano",
                    y="taxa_10000",
                    points=points_mode,
                    hover_data={
                        "territorio": True,
                        "vinculos": ":,.0f",
                        "populacao": ":,.0f",
                        "taxa_10000": ":.2f",
                        "ano": True,
                    },
                    title=(
                        f"Distribuição territorial — {CATEGORIA_SB_NOMES.get(categoria_territorio, categoria_territorio)} "
                        f"em {nivel_territorial.lower()}"
                    ),
                    labels={
                        "ano": "Ano",
                        "taxa_10000": "Vínculos por 10 mil habitantes",
                    },
                )
                fig.update_traces(boxmean=True, jitter=0.25)

            fig.update_xaxes(type="category")
            if escala_box == "Logarítmica":
                fig.update_yaxes(type="log")
            elif ymax is not None and pd.notna(ymax) and ymax > 0:
                fig.update_yaxes(range=[0, ymax * 1.08])
            fig.update_layout(height=560, showlegend=False)
            plot(fig)

            st.markdown(
                '<div class="ow-small">'
                'Leitura sugerida: o violino mostra a concentração da distribuição; a caixa interna resume mediana e quartis. '
                'Use o ranking e os mapas abaixo para entender quais territórios explicam os extremos.'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown("### Ranking territorial no ano selecionado")

            rank = ref.sort_values("taxa_10000", ascending=False).head(limite_ranking).copy()
            rank_plot = rank.sort_values("taxa_10000", ascending=True)

            fig = px.bar(
                rank_plot,
                x="taxa_10000",
                y="territorio",
                orientation="h",
                text="taxa_10000",
                hover_data={
                    "vinculos": ":,.0f",
                    "populacao": ":,.0f",
                    "taxa_10000": ":.2f",
                },
                title=(
                    f"Maiores densidades — {CATEGORIA_SB_NOMES.get(categoria_territorio, categoria_territorio)}, "
                    f"{ano_territorio}"
                ),
                labels={
                    "taxa_10000": "Vínculos por 10 mil habitantes",
                    "territorio": "",
                },
            )
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig.update_layout(height=max(520, 24 * len(rank_plot) + 180), showlegend=False)
            plot(fig)

            st.markdown("### Mapas coropléticos da distribuição espacial")

            mc1, mc2, mc3 = st.columns([1.0, 1.0, 1.0])

            with mc1:
                mapa_nivel = st.selectbox(
                    "Nível do mapa",
                    ["UF", "Município"],
                    index=0,
                    help="O mapa municipal pode ficar pesado se muitas UFs estiverem selecionadas.",
                )

            with mc2:
                mapa_metrica = st.selectbox(
                    "Métrica do mapa",
                    ["Vínculos por 10 mil hab.", "Vínculos absolutos"],
                    index=0,
                )

            with mc3:
                mapa_escala = st.selectbox(
                    "Escala do mapa",
                    ["Linear", "Logarítmica (transformada)"],
                    index=0,
                )

            map_df = build_territory_summary(mapa_nivel, categoria_territorio)
            map_df = map_df[map_df["ano"] == ano_territorio].copy()

            if mapa_metrica == "Vínculos absolutos":
                map_df["valor_mapa"] = map_df["vinculos"]
                legenda = "Vínculos"
            else:
                map_df["valor_mapa"] = map_df["taxa_10000"]
                legenda = "Vínculos por 10 mil hab."

            if mapa_escala.startswith("Log"):
                map_df["valor_mapa_plot"] = map_df["valor_mapa"].fillna(0).apply(lambda x: 0 if x <= 0 else __import__("math").log10(x + 1))
                legenda_plot = f"log10({legenda} + 1)"
            else:
                map_df["valor_mapa_plot"] = map_df["valor_mapa"]
                legenda_plot = legenda

            if mapa_nivel == "UF":
                geojson_obj, geo_src = load_geojson("uf")
                loc_col = "sg_uf"
                top_cols = ["territorio", "vinculos", "populacao", "taxa_10000"]
            else:
                geojson_obj, geo_src = load_geojson("municipio")
                loc_col = "cod_municipio"
                top_cols = ["territorio", "sg_uf", "vinculos", "populacao", "taxa_10000"]

            if geojson_obj is None:
                st.warning("GeoJSON não encontrado. Para os mapas, mantenha os arquivos de limites em assets/br_ufs.geojson e assets/br_municipios.geojson.")
            else:
                st.caption(f"Base cartográfica: {geo_src}")

                fig = px.choropleth(
                    map_df,
                    geojson=geojson_obj,
                    locations=loc_col,
                    featureidkey="properties.__match",
                    color="valor_mapa_plot",
                    hover_name="territorio",
                    hover_data={
                        "vinculos": ":,.0f",
                        "populacao": ":,.0f",
                        "taxa_10000": ":.2f",
                        "valor_mapa_plot": False,
                        loc_col: False,
                    },
                    projection="mercator",
                    title=(
                        f"Distribuição espacial — {CATEGORIA_SB_NOMES.get(categoria_territorio, categoria_territorio)}, "
                        f"{ano_territorio} ({legenda.lower()})"
                    ),
                    labels={"valor_mapa_plot": legenda_plot},
                )
                fig.update_geos(fitbounds="locations", visible=False)
                fig.update_layout(height=700, margin=dict(l=10, r=10, t=70, b=10))
                plot(fig)

                c_map1, c_map2 = st.columns([1.1, 0.9])
                with c_map1:
                    map_rank = map_df.sort_values("valor_mapa", ascending=False)[top_cols + ["valor_mapa"]].head(20).copy()
                    rename_cols = {
                        "territorio": "Território",
                        "sg_uf": "UF",
                        "vinculos": "Vínculos",
                        "populacao": "População",
                        "taxa_10000": "Vínculos por 10 mil hab.",
                        "valor_mapa": legenda,
                    }
                    map_rank = map_rank.rename(columns=rename_cols)
                    show_cols = [c for c in ["Território", "UF", legenda, "Vínculos", "População", "Vínculos por 10 mil hab."] if c in map_rank.columns]
                    show_table(map_rank[show_cols], height=360)

                with c_map2:
                    fig = px.scatter(
                        ref,
                        x="populacao",
                        y="taxa_10000",
                        size=ref["vinculos"].clip(lower=1),
                        hover_name="territorio",
                        hover_data={
                            "vinculos": ":,.0f",
                            "populacao": ":,.0f",
                            "taxa_10000": ":.2f",
                        },
                        title=f"População × densidade — {ano_territorio}",
                        labels={
                            "populacao": "População",
                            "taxa_10000": "Vínculos por 10 mil hab.",
                        },
                    )
                    fig.update_xaxes(type="log")
                    fig.update_layout(height=360)
                    plot(fig)

            st.markdown("### Tabela territorial")

            table = ref.sort_values("taxa_10000", ascending=False).copy()
            table_out = table.rename(
                columns={
                    "ano": "Ano",
                    "territorio": "Território",
                    "vinculos": "Vínculos",
                    "populacao": "População",
                    "taxa_10000": "Vínculos por 10 mil hab.",
                    "nivel_territorial": "Nível territorial",
                    "categoria": "Categoria",
                    "sg_uf": "UF",
                    "regiao_de_saude": "Região de saúde",
                    "macrorregiao_de_saude": "Macrorregião de saúde",
                    "cod_municipio": "Código município",
                    "municipio_label": "Município",
                }
            )

            cols_show = [
                "Ano",
                "Nível territorial",
                "Categoria",
                "UF",
                "Território",
                "Vínculos",
                "População",
                "Vínculos por 10 mil hab.",
            ]
            cols_show = [c for c in cols_show if c in table_out.columns]
            show_table(table_out[cols_show], height=420)

            download_buttons(
                table_out,
                "territorio_mapas_densidades_saude_bucal",
                {
                    "ano_selecionado": table_out,
                    "serie_completa": terr_df.rename(
                        columns={
                            "ano": "Ano",
                            "territorio": "Território",
                            "vinculos": "Vínculos",
                            "populacao": "População",
                            "taxa_10000": "Vínculos por 10 mil hab.",
                            "nivel_territorial": "Nível territorial",
                            "categoria": "Categoria",
                        }
                    ),
                    "mapa_ano": map_df.rename(
                        columns={
                            "ano": "Ano",
                            "territorio": "Território",
                            "vinculos": "Vínculos",
                            "populacao": "População",
                            "taxa_10000": "Vínculos por 10 mil hab.",
                            "valor_mapa": legenda,
                        }
                    ),
                },
            )



with tabs[3]:
    st.markdown('<div class="ow-section-title">Ocupações odontológicas detalhadas</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ow-note">'
        'Esta aba mantém o detalhamento por CBO individual. A síntese no padrão CD, TSB, ASB, TPD e APD fica na primeira aba, '
        'seguindo o modelo analítico de Saúde Bucal.'
        '</div>',
        unsafe_allow_html=True,
    )

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
                CAST({q(municipio_col)} AS VARCHAR) AS cod_municipio_raw,
                REGEXP_REPLACE(CAST({q(cbo_col)} AS VARCHAR), '[^0-9]', '', 'g') AS cbo,
                COUNT(*) AS vinculos
            FROM {TABLE}
            WHERE {where_sql}
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3
        """)
        if not cbo_mun.empty:
            terr_cols = municipal_panel[["ano", "cod_municipio", "populacao_usada"]].drop_duplicates()
            valid_codes_cbo = set(terr_cols["cod_municipio"].astype(str).tolist())
            if "cod_municipio_raw" in cbo_mun.columns:
                cbo_mun["cod_municipio"] = cbo_mun["cod_municipio_raw"].apply(
                    lambda x: normalize_municipio_code_validated(x, valid_codes_cbo)
                )
            else:
                cbo_mun["cod_municipio"] = cbo_mun["cod_municipio"].apply(
                    lambda x: normalize_municipio_code_validated(x, valid_codes_cbo)
                )
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

    st.markdown(
        '<div class="ow-note">'
        'V5.1: esta aba agora detecta automaticamente colunas de vínculo, natureza jurídica, CNAE e setor. '
        'Também mostra diagnóstico de preenchimento para evitar gráficos vazios sem explicação.'
        '</div>',
        unsafe_allow_html=True,
    )

    def candidate_sector_columns(all_cols: list[str]) -> list[str]:
        tokens = [
            "tipo_vinculo", "tipo vínculo", "vinculo", "vínculo",
            "natureza", "juridica", "jurídica",
            "cnae", "classe", "divisao", "divisão",
            "setor", "subsetor", "atividade", "estabelecimento"
        ]

        out = []
        for c in all_cols:
            low = str(c).lower()
            if any(t in low for t in tokens):
                out.append(c)

        # Remove variáveis que costumam não ser setor/vínculo, mas entram por palavra solta.
        bad_tokens = ["desligamento", "admissao", "admissão", "municipio", "município"]
        out = [c for c in out if not any(bt in str(c).lower() for bt in bad_tokens)]
        return out

    def classify_sector_column(col: str) -> tuple[str, Any]:
        low = str(col).lower()

        if "tipo" in low and ("vinc" in low or "vínc" in low):
            return "Tipo de vínculo", decode_tipo_vinculo

        if "natureza" in low:
            return "Natureza jurídica", decode_natureza_detalhe

        if "cnae" in low or "classe" in low or "divis" in low or "atividade" in low:
            return "CNAE / setor econômico", decode_cnae

        if "setor" in low or "subsetor" in low:
            return "Setor", lambda x: str(x).strip().title() if str(x).strip() else "Não informado"

        return f"Variável setorial: {col}", lambda x: str(x).strip().title() if str(x).strip() else "Não informado"

    setor_candidates = candidate_sector_columns(cols)

    if not setor_candidates:
        st.warning("Não localizei colunas candidatas para setor/vínculo. Veja a lista de colunas originais na aba Exportações.")
    else:
        diag_rows = []

        for col in setor_candidates:
            diag = sql_df(f"""
                SELECT
                    '{col}' AS coluna_original,
                    COUNT(*) AS registros,
                    SUM(CASE WHEN {q(col)} IS NOT NULL AND TRIM(CAST({q(col)} AS VARCHAR)) <> '' THEN 1 ELSE 0 END) AS nao_nulos,
                    COUNT(DISTINCT CAST({q(col)} AS VARCHAR)) AS categorias_distintas
                FROM {TABLE}
                WHERE {where_sql}
            """)
            diag_rows.append(diag)

        setor_diag = pd.concat(diag_rows, ignore_index=True)
        setor_diag["percentual_preenchido"] = setor_diag["nao_nulos"] / setor_diag["registros"].replace(0, pd.NA) * 100

        st.markdown("### Diagnóstico das colunas candidatas")
        show_table(friendly_columns(setor_diag), height=260)

        usable = setor_diag[setor_diag["nao_nulos"] > 0].copy()

        if usable.empty:
            st.warning(
                "As colunas candidatas existem, mas retornaram zero valores preenchidos com os filtros atuais. "
                "Teste remover filtros de CBO, UF, sexo/raça ou ampliar o período."
            )
        else:
            usable = usable.sort_values(["nao_nulos", "categorias_distintas"], ascending=False)

            options = []
            option_map = {}

            for col in usable["coluna_original"].tolist():
                label_kind, decoder = classify_sector_column(col)
                option = f"{label_kind} — coluna `{col}`"
                options.append(option)
                option_map[option] = (col, label_kind, decoder)

            selected_option = st.selectbox("Escolha a variável de setor/vínculo", options)
            dim_col, dim_name, decoder = option_map[selected_option]

            raw = sql_df(f"""
                SELECT
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    CAST({q(dim_col)} AS VARCHAR) AS categoria_original,
                    COUNT(*) AS vinculos,
                    COUNT(DISTINCT {mun_key_expr(municipio_col)}) AS municipios
                FROM {TABLE}
                WHERE {where_sql}
                  AND {q(dim_col)} IS NOT NULL
                  AND TRIM(CAST({q(dim_col)} AS VARCHAR)) <> ''
                GROUP BY 1, 2
                ORDER BY 1, 3 DESC
            """)

            if raw.empty:
                st.warning(f"A coluna `{dim_col}` existe, mas a consulta retornou vazia para os filtros atuais.")
            else:
                raw["categoria"] = raw["categoria_original"].apply(decoder)

                setor = (
                    raw.groupby(["ano", "categoria"], as_index=False)
                    .agg(
                        vinculos=("vinculos", "sum"),
                        municipios=("municipios", "max"),
                    )
                )

                top = (
                    setor.groupby("categoria")["vinculos"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(max_categories)
                    .index
                )

                plot_df = setor.copy()
                plot_df["categoria_plot"] = plot_df["categoria"].where(plot_df["categoria"].isin(top), "Outros")
                plot_df = plot_df.groupby(["ano", "categoria_plot"], as_index=False)["vinculos"].sum()

                available_years = sorted(plot_df["ano"].dropna().astype(int).unique().tolist())

                if not available_years:
                    st.warning("Não há anos disponíveis para a variável selecionada.")
                else:
                    selected_year = st.selectbox("Ano de destaque", available_years, index=len(available_years) - 1)

                    last_df = (
                        plot_df[plot_df["ano"] == selected_year]
                        .sort_values("vinculos", ascending=True)
                        .copy()
                    )

                    st.markdown(f"### Distribuição — {dim_name} em {selected_year}")

                    fig = px.bar(
                        last_df,
                        x="vinculos",
                        y="categoria_plot",
                        orientation="h",
                        text="vinculos",
                        title=f"{dim_name} — vínculos em {selected_year}",
                        labels={"vinculos": "Vínculos", "categoria_plot": ""},
                    )
                    fig.update_layout(height=max(480, 30 * len(last_df) + 180), showlegend=False)
                    plot(fig)

                    st.markdown("### Evolução temporal")

                    fig = px.line(
                        plot_df,
                        x="ano",
                        y="vinculos",
                        color="categoria_plot",
                        markers=True,
                        title=f"Evolução temporal — {dim_name}",
                        labels={"ano": "Ano", "vinculos": "Vínculos", "categoria_plot": ""},
                    )
                    fig.update_xaxes(dtick=1)
                    plot(fig)

                    st.markdown("### Composição percentual")

                    totals = plot_df.groupby("ano", as_index=False)["vinculos"].sum().rename(columns={"vinculos": "total"})
                    pct = plot_df.merge(totals, on="ano", how="left")
                    pct["percentual"] = pct["vinculos"] / pct["total"].replace(0, pd.NA) * 100

                    fig = px.area(
                        pct,
                        x="ano",
                        y="percentual",
                        color="categoria_plot",
                        title=f"Composição percentual — {dim_name}",
                        labels={"ano": "Ano", "percentual": "% dos vínculos", "categoria_plot": ""},
                    )
                    fig.update_xaxes(dtick=1)
                    plot(fig)

                    setor_out = setor.rename(
                        columns={
                            "ano": "Ano",
                            "categoria": "Categoria",
                            "vinculos": "Vínculos",
                            "municipios": "Municípios",
                        }
                    )

                    raw_out = raw.rename(
                        columns={
                            "ano": "Ano",
                            "categoria_original": "Categoria original",
                            "categoria": "Categoria",
                            "vinculos": "Vínculos",
                            "municipios": "Municípios",
                        }
                    )

                    if show_raw_tables:
                        st.markdown("### Tabela consolidada")
                        show_table(setor_out, height=360)

                        with st.expander("Categorias originais encontradas na RAIS", expanded=False):
                            show_table(raw_out, height=360)

                    download_buttons(
                        setor_out,
                        "setor_vinculo_v51",
                        {
                            "setor_vinculo": setor_out,
                            "categorias_originais": raw_out,
                            "diagnostico": friendly_columns(setor_diag),
                        },
                    )




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

    st.markdown(
        '<div class="ow-note">'
        'V5.1: esta aba agora procura automaticamente colunas monetárias/salariais, diagnostica valores válidos '
        'e informa quando os filtros atuais deixam a consulta sem dados.'
        '</div>',
        unsafe_allow_html=True,
    )

    def candidate_salary_columns(all_cols: list[str]) -> list[str]:
        tokens = [
            "remun", "remuner", "salario", "salário", "renda",
            "vl_", "valor", "media_nom", "média nom", "nominal"
        ]
        bad = ["municipio", "município", "vinculo", "vínculo"]
        out = []
        for c in all_cols:
            low = str(c).lower()
            if any(t in low for t in tokens) and not any(b in low for b in bad):
                out.append(c)
        return out

    salary_candidates = candidate_salary_columns(cols)

    if not salary_candidates:
        st.warning("Nenhuma coluna candidata a salário/remuneração foi detectada no banco.")
        st.markdown("#### Colunas existentes")
        show_table(pd.DataFrame({"coluna": cols}), height=360)
    else:
        diagnostics = []

        for col in salary_candidates:
            expr = numeric_expr(col)

            d = sql_df(f"""
                SELECT
                    '{col}' AS coluna,
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    COUNT(*) AS registros,
                    SUM(CASE WHEN {q(col)} IS NOT NULL AND TRIM(CAST({q(col)} AS VARCHAR)) <> '' THEN 1 ELSE 0 END) AS preenchidos,
                    SUM(CASE WHEN {expr} IS NOT NULL THEN 1 ELSE 0 END) AS numericos,
                    SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS positivos,
                    AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS media_positivos,
                    MIN(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS minimo_positivo,
                    MAX(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS maximo_positivo
                FROM {TABLE}
                WHERE {where_sql}
                GROUP BY 1, 2
                ORDER BY 2
            """)
            diagnostics.append(d)

        diag = pd.concat(diagnostics, ignore_index=True)
        diag["percentual_positivo"] = diag["positivos"] / diag["registros"].replace(0, pd.NA) * 100

        st.markdown("### Diagnóstico das colunas salariais")
        show_table(friendly_columns(diag), height=300)

        col_scores = (
            diag.groupby("coluna", as_index=False)
            .agg(
                positivos=("positivos", "sum"),
                numericos=("numericos", "sum"),
                preenchidos=("preenchidos", "sum"),
                media=("media_positivos", "mean"),
            )
            .sort_values(["positivos", "numericos", "preenchidos"], ascending=False)
        )

        usable_cols = col_scores[col_scores["positivos"] > 0]["coluna"].tolist()

        if not usable_cols:
            st.warning(
                "Foram encontradas colunas salariais candidatas, mas nenhuma possui valores numéricos positivos "
                "com os filtros atuais. Tente remover filtros ou verificar se o ETL leu a remuneração."
            )
        else:
            selected_salary_col = st.selectbox(
                "Coluna salarial para análise",
                usable_cols,
                index=0,
                help="A primeira opção é a coluna com mais valores positivos nos filtros atuais.",
            )

            expr = numeric_expr(selected_salary_col)

            sal = sql_df(f"""
                SELECT
                    CAST({q(ano_col)} AS INTEGER) AS ano,
                    COUNT(*) AS registros,
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

            st.markdown(f"### Resumo anual — `{selected_salary_col}`")
            show_table(friendly_columns(sal), height=260)

            plot_df = sal.dropna(subset=["remuneracao_media"]).copy()

            if plot_df.empty:
                st.warning("A coluna selecionada existe, mas não há média anual calculável para os filtros atuais.")
            else:
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

            # Distribuição por UF ou território, se possível.
            if uf_col_db:
                sal_uf = sql_df(f"""
                    SELECT
                        CAST({q(ano_col)} AS INTEGER) AS ano,
                        CAST({q(uf_col_db)} AS VARCHAR) AS uf,
                        SUM(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN 1 ELSE 0 END) AS registros_validos,
                        AVG(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_media,
                        MEDIAN(CASE WHEN {expr} IS NOT NULL AND {expr} > 0 THEN {expr} ELSE NULL END) AS remuneracao_mediana
                    FROM {TABLE}
                    WHERE {where_sql}
                    GROUP BY 1, 2
                    HAVING registros_validos > 0
                    ORDER BY 1, 4 DESC
                """)

                if not sal_uf.empty:
                    st.markdown("### Comparação entre UFs")

                    fig = px.box(
                        sal_uf,
                        x="ano",
                        y="remuneracao_media",
                        points="all",
                        title="Variação da remuneração média entre UFs",
                        labels={"ano": "Ano", "remuneracao_media": "Remuneração média"},
                    )
                    fig.update_xaxes(type="category")
                    plot(fig)

                    if show_raw_tables:
                        show_table(friendly_columns(sal_uf), height=320)

            download_buttons(
                friendly_columns(sal),
                "panorama_salarial_v51",
                {
                    "salario_ano": friendly_columns(sal),
                    "diagnostico_salario": friendly_columns(diag),
                    "ranking_colunas": friendly_columns(col_scores),
                },
            )



with tabs[7]:
    st.markdown('<div class="ow-section-title">Exportações e auditoria</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ow-note">As tabelas abaixo são úteis para auditar filtros, anos, populações usadas e códigos originais.</div>',
        unsafe_allow_html=True,
    )

    export_tables = {"serie_temporal": friendly_columns(series_df)}

    if not municipal_panel.empty:
        integracao_municipal = (
            municipal_panel.groupby("ano", as_index=False)
            .agg(
                vinculos_integrados_municipio=("vinculos", "sum"),
                municipios_grade=("cod_municipio", "nunique"),
                municipios_com_vinculo=("vinculos", lambda x: (x > 0).sum()),
                populacao_usada=("populacao_usada", "sum"),
            )
            .merge(series_df[["ano", "vinculos"]].rename(columns={"vinculos": "vinculos_banco"}), on="ano", how="left")
        )
        integracao_municipal["diferenca_banco_municipios"] = (
            integracao_municipal["vinculos_banco"] - integracao_municipal["vinculos_integrados_municipio"]
        )
        integracao_municipal["percentual_integrado"] = (
            integracao_municipal["vinculos_integrados_municipio"] /
            integracao_municipal["vinculos_banco"].replace(0, pd.NA) * 100
        )

        export_tables["municipios_taxas"] = friendly_columns(municipal_panel)
        export_tables["diagnostico_integracao_municipal"] = friendly_columns(integracao_municipal)
    export_tables["cbo_filtrados"] = friendly_columns(cbo_filtered)
    export_tables["colunas_banco"] = pd.DataFrame({"Coluna original": cols})

    show_table(export_tables["serie_temporal"])
    download_buttons(export_tables["serie_temporal"], "exportacao_geral_v6_0_saude_bucal_2", export_tables)

    if "diagnostico_integracao_municipal" in export_tables:
        st.markdown("### Diagnóstico da integração município-população")
        st.markdown(
            '<div class="ow-note">'
            'Esta tabela compara os vínculos totais do banco com os vínculos que entraram na grade município-ano. '
            'O percentual integrado deve ficar próximo de 100%. Se ficar muito baixo em algum ano, há problema de código municipal.'
            '</div>',
            unsafe_allow_html=True,
        )
        show_table(export_tables["diagnostico_integracao_municipal"], height=260)

    st.markdown("### Diagnóstico dos códigos municipais originais")
    cod_diag = municipio_code_diagnostics()
    show_table(friendly_columns(cod_diag), height=260)
    export_tables["diagnostico_codigos_municipio"] = friendly_columns(cod_diag)

    with st.expander("Colunas originais do banco", expanded=False):
        show_table(export_tables["colunas_banco"])

    with st.expander("CBOs disponíveis após os filtros", expanded=False):
        show_table(export_tables["cbo_filtrados"], height=420)


st.markdown(
    '<div class="ow-footer">OdontoWorkforce Brasil V6.0 Saúde Bucal — painel experimental para análise de força de trabalho odontológica com RAIS, regiões de saúde e populações IBGE/TCU.</div>',
    unsafe_allow_html=True,
)
