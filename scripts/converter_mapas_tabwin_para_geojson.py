
from __future__ import annotations

from pathlib import Path
import json
import struct
import zipfile

PROJECT_DIR = Path(r"C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3")
MAPAS_ZIP = PROJECT_DIR / "mapas.zip"
MAP_DIR = PROJECT_DIR / "assets" / "mapas_tabwin"
OUT_DIR = PROJECT_DIR / "assets"

UF_CODE_TO_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def maybe_make_valid(geometry: dict) -> dict:
    """
    Tenta corrigir autointerseções se shapely estiver instalado.
    Se não estiver, mantém a geometria original.
    """
    try:
        from shapely.geometry import shape, mapping
        from shapely.validation import make_valid
        from shapely.ops import unary_union
    except Exception:
        return geometry

    geom = shape(geometry)
    if geom.is_valid:
        return geometry

    fixed = make_valid(geom)
    if fixed.geom_type == "GeometryCollection":
        polys = [g for g in fixed.geoms if g.geom_type in ("Polygon", "MultiPolygon") and not g.is_empty]
        if polys:
            fixed = unary_union(polys)

    if fixed.is_empty:
        return geometry

    return mapping(fixed)


def parse_tabwin_map(path: Path, kind: str) -> dict:
    data = path.read_bytes()
    pos = 18
    features = []
    total = len(data)

    while pos < total:
        if pos + 48 > total:
            break

        code_raw = data[pos + 2:pos + 8].split(b"\x00")[0].decode("latin1", "ignore").strip()
        name = data[pos + 13:pos + 38].decode("latin1", "ignore").strip()

        # Estes dois floats são o ponto de rótulo/centróide usado pelo TabWin.
        # NÃO são vértices do polígono. Incluí-los no anel distorce o mapa.
        label_lon, label_lat = struct.unpack("<ff", data[pos + 38:pos + 46])

        n = struct.unpack("<H", data[pos + 46:pos + 48])[0]
        off = pos + 48

        if off + n * 8 > total:
            raise ValueError(f"Registro inválido em {pos}, código={code_raw}, pontos={n}")

        coords = []
        for i in range(n):
            x, y = struct.unpack("<ff", data[off + i * 8: off + i * 8 + 8])
            coords.append([float(x), float(y)])

        if len(coords) >= 3:
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            if kind == "uf":
                cod_uf = code_raw[:2]
                sigla = UF_CODE_TO_SIGLA.get(cod_uf, cod_uf)
                props = {
                    "cod_uf": cod_uf,
                    "sg_uf": sigla,
                    "nome": name,
                    "cod_original": code_raw,
                    "match_id": sigla,
                    "label_lon": float(label_lon),
                    "label_lat": float(label_lat),
                }
            else:
                cod_mun = code_raw[:6]
                props = {
                    "cod_municipio": cod_mun,
                    "nome": name,
                    "cod_original": cod_mun,
                    "match_id": cod_mun,
                    "label_lon": float(label_lon),
                    "label_lat": float(label_lat),
                }

            geom = {"type": "Polygon", "coordinates": [coords]}
            geom = maybe_make_valid(geom)

            features.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": geom,
                }
            )

        pos = off + n * 8

    return {"type": "FeatureCollection", "features": features}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MAP_DIR.mkdir(parents=True, exist_ok=True)

    if MAPAS_ZIP.exists():
        with zipfile.ZipFile(MAPAS_ZIP) as z:
            z.extractall(MAP_DIR)

    br_uf = MAP_DIR / "br_uf.MAP"
    br_mun = MAP_DIR / "br_municip.MAP"

    if not br_uf.exists() or not br_mun.exists():
        raise FileNotFoundError(
            "Não encontrei br_uf.MAP e br_municip.MAP. Copie mapas.zip para a pasta do projeto "
            "ou coloque os arquivos .MAP em assets/mapas_tabwin."
        )

    uf_geo = parse_tabwin_map(br_uf, "uf")
    mun_geo = parse_tabwin_map(br_mun, "municipio")

    (OUT_DIR / "br_ufs.geojson").write_text(
        json.dumps(uf_geo, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (OUT_DIR / "br_municipios.geojson").write_text(
        json.dumps(mun_geo, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print("GeoJSONs gerados:")
    print(OUT_DIR / "br_ufs.geojson", len(uf_geo["features"]), "feições")
    print(OUT_DIR / "br_municipios.geojson", len(mun_geo["features"]), "feições")


if __name__ == "__main__":
    main()
