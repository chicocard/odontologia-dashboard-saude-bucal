
from __future__ import annotations

from pathlib import Path
import json

PROJECT_DIR = Path(r"C:\Projetos\odontologia_workforce_app\odontologia_dashboard_v3")
ASSETS = PROJECT_DIR / "assets"

for name in ["br_ufs.geojson", "br_municipios.geojson"]:
    p = ASSETS / name
    print("\n", "=" * 80)
    print(name)
    print("Existe:", p.exists())
    print("Caminho:", p)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        features = data.get("features", [])
        print("Feições:", len(features))
        if features:
            print("Propriedades da primeira feição:")
            print(features[0].get("properties", {}))
            xs, ys = [], []
            for feat in features[:50]:
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                if geom.get("type") == "Polygon":
                    rings = coords
                elif geom.get("type") == "MultiPolygon":
                    rings = [ring for poly in coords for ring in poly]
                else:
                    rings = []
                for ring in rings:
                    for pair in ring[:50]:
                        if len(pair) >= 2:
                            xs.append(pair[0])
                            ys.append(pair[1])
            if xs and ys:
                print("Faixa longitude:", min(xs), "a", max(xs))
                print("Faixa latitude:", min(ys), "a", max(ys))
