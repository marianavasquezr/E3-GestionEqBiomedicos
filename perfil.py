#!/usr/bin/env python3
"""Perfil de la fuente (S4): las cinco preguntas sobre el bruto del 19/11.
Uso, en la carpeta del repositorio:  python3 perfil.py | tee perfil_salida.txt
No cambia el bruto: solo lo lee y cuenta."""
import glob
import json
import re
import unicodedata

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)

# --- Ajustes: revísenlos después de ver la sección 0 y la 2 ---
FSOL = "fecha_solicitud"   # fecha que define el mes de una orden
DIA_PRIMERO = True         # True: 04/09 = 4 de septiembre · False: 9 de abril
CORTE = pd.Timestamp("2026-11-19")
SIS = [":id", ":created_at", ":updated_at"]


def cargar(nombre):
    ruta = sorted(glob.glob(f"data/raw/{nombre}_*.json"))[-1]
    df = pd.DataFrame(json.load(open(ruta, encoding="utf-8")))
    print(f"Bruto: {ruta} · filas: {len(df)}")
    return df


def titulo(t):
    print("\n" + "=" * 72 + "\n" + t + "\n" + "=" * 72)


def patron(v):
    """'2026-04-09' -> '9999-99-99' ; '04/09/2026' -> '99/99/9999'."""
    if pd.isna(v):
        return "<nulo>"
    return re.sub(r"[A-Za-z]", "a", re.sub(r"\d", "9", str(v)))


def norm_txt(v):
    """Minúsculas, sin tildes, sin espacios de sobra."""
    if pd.isna(v):
        return v
    s = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def a_fecha(s):
    """ISO (2026-04-09...) por un lado; el resto con DIA_PRIMERO. Lo que no se pueda, NaT."""
    s = s.astype("string").str.strip()
    es_iso = s.str.match(r"^\d{4}-", na=False)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    out[es_iso] = pd.to_datetime(s[es_iso], format="ISO8601", errors="coerce")
    otras = ~es_iso & s.notna()
    out[otras] = pd.to_datetime(s[otras], format="mixed", dayfirst=DIA_PRIMERO, errors="coerce")
    return out


o = cargar("ordenes")
e = cargar("equipos")

# ---------------------------------------------------------------------------
titulo("0 · Qué columnas llegaron")
print("ordenes:", o.columns.tolist())
print("equipos:", e.columns.tolist())
print("\nPrimeras 3 órdenes:\n", o.head(3).T)
print("\nNulos y valores distintos por columna (ordenes):")
print(pd.DataFrame({"nulos": o.isna().sum(), "distintos": o.nunique()}))

# ---------------------------------------------------------------------------
titulo("1 · id_orden repetidos")
d = o.drop(columns=SIS, errors="ignore")
print("filas:", len(o), "· id_orden distintos:", o["id_orden"].nunique())
rep = d[d.duplicated("id_orden", keep=False)].sort_values("id_orden")
print("filas que repiten id_orden:", len(rep), "· id_orden afectados:", rep["id_orden"].nunique())
print("copias exactas sobrantes en toda la tabla:", int(d.duplicated(keep="first").sum()))

tipos = {}
for i, g in rep.groupby("id_orden"):
    g = g.fillna("<nulo>")
    cambian = [c for c in g.columns if g[c].nunique() > 1]
    if not cambian:
        tipos[i] = "copia exacta"
    elif cambian == ["fecha_registro"]:
        tipos[i] = "solo fecha_registro"
    else:
        tipos[i] = "otra columna: " + ", ".join(cambian)
tipos = pd.Series(tipos, name="grupo", dtype="object")
res = pd.DataFrame({"ids": tipos.value_counts(), "filas": rep["id_orden"].map(tipos).value_counts()})
res["filas_sobrantes"] = res["filas"] - res["ids"]
print("\n", res)

for col in [c for c in o.columns if "sede" in c.lower()]:
    print(f"\nGrupo vs {col}:")
    print(pd.crosstab(rep["id_orden"].map(tipos), rep[col].fillna("<nulo>")))

for t in tipos.unique():
    ejemplo = tipos[tipos == t].index[0]
    print(f"\nEjemplo «{t}» (id_orden {ejemplo}):")
    print(rep[rep["id_orden"] == ejemplo].T)

# ---------------------------------------------------------------------------
titulo("2 · Formatos de fecha")
fechas = [c for c in o.columns if c.lower().startswith("fecha")]
for c in fechas:
    print(f"\n{c}:")
    print(o[c].map(patron).value_counts(dropna=False))

pat = o[FSOL].map(patron)
print(f"\n¿Qué columna explica el formato de {FSOL}? (columnas con pocos valores)")
for col in [c for c in o.columns if c not in fechas and 1 < o[c].nunique() <= 15]:
    print(f"\n-- {col}")
    print(pd.crosstab(o[col].fillna("<nulo>"), pat))

print("\nFechas con '/': ¿día o mes primero?")
for c in fechas:
    s = o[c].dropna().astype(str)
    b = s[s.str.match(r"^\d{1,2}/\d{1,2}/\d{4}")]
    if b.empty:
        continue
    p = b.str.extract(r"^(\d{1,2})/(\d{1,2})/").astype(int)
    print(f"{c}: con '/': {len(b)} · ambiguas (ambos ≤12): {int(((p[0] <= 12) & (p[1] <= 12)).sum())}"
          f" · 1er número >12: {int((p[0] > 12).sum())} · 2º número >12: {int((p[1] > 12).sum())}")

print("\nEl 04/09:")
for dp in (True, False):
    print(f"  dayfirst={dp}: {pd.to_datetime('04/09/2026', dayfirst=dp).date()}")
for c in fechas:
    m = o[c].astype("string").str.contains(r"^0?4/0?9/", na=False)
    if m.any():
        print(f"  {c}: {int(m.sum())} filas con 04/09 ->", o.loc[m, ["id_orden", c]].head(5).to_dict("records"))

# ---------------------------------------------------------------------------
titulo("3 · Variantes de tipo_mantenimiento, prioridad y equipo_fuera_servicio")
for c in ["tipo_mantenimiento", "prioridad", "equipo_fuera_servicio"]:
    if c not in o:
        print(f"(no existe la columna {c})")
        continue
    print(f"\n{c}: {o[c].nunique(dropna=False)} formas tal como llegan · "
          f"{o[c].map(norm_txt).nunique(dropna=False)} sin tildes/mayúsculas/espacios")
    print(o[c].value_counts(dropna=False))

tm = o["tipo_mantenimiento"]
es_corr = tm.map(norm_txt).str.startswith("correct", na=False)
canon = tm[es_corr].value_counts().idxmax()
mes = a_fecha(o[FSOL]).dt.to_period("M").astype(str)
t = pd.DataFrame({
    "correctivos_unificados": es_corr.groupby(mes).sum(),
    f"solo_'{canon}'": (tm == canon).groupby(mes).sum(),
})
t["por_fuera"] = t.iloc[:, 0] - t.iloc[:, 1]
print(f"\nCorrectivos por mes de {FSOL} (contando solo «{canon}» vs unificando):")
print(t)

# ---------------------------------------------------------------------------
titulo("4 · id_equipo que no está en el inventario")
inv = set(e["id_equipo"].dropna())
huerf = o[~o["id_equipo"].isin(inv)]
print("órdenes sin equipo en inventario:", len(huerf),
      "· id_equipo distintos:", huerf["id_equipo"].nunique(),
      "· id_equipo nulo:", int(o["id_equipo"].isna().sum()))
print("\nFormato en inventario:\n", e["id_equipo"].map(patron).value_counts())
print("\nFormato en las órdenes huérfanas:\n", huerf["id_equipo"].map(patron).value_counts(dropna=False))


def clave(v):
    """Letras en mayúscula + número sin ceros a la izquierda: 'eq 0012' -> 'EQ|12'."""
    if pd.isna(v):
        return None
    s = str(v).upper()
    num = re.sub(r"\D", "", s)
    return re.sub(r"[^A-Z]", "", s) + "|" + (str(int(num)) if num else "")


claves_inv = e["id_equipo"].map(clave)
print("\nclaves repetidas en el inventario (deben ser 0):", int(claves_inv.duplicated().sum()))
mapa = dict(zip(claves_inv, e["id_equipo"]))
recup = huerf["id_equipo"].map(clave).map(mapa)
print("recuperables con regla de formato:", int(recup.notna().sum()),
      "· no recuperables:", int(recup.isna().sum()))
print("\nEjemplos recuperados (original -> inventario):")
print(pd.DataFrame({"original": huerf["id_equipo"], "inventario": recup})[recup.notna()]
      .drop_duplicates().head(15).to_string(index=False))
print("\nNo recuperables (id_equipo: órdenes):")
print(huerf.loc[recup.isna(), "id_equipo"].value_counts(dropna=False).to_string())

# ---------------------------------------------------------------------------
titulo("5 · Valores que no convierten y fechas imposibles")
for nombre, df in (("ordenes", o), ("equipos", e)):
    for c in df.columns:
        if c in SIS or c.lower().startswith("fecha"):
            continue
        s = df[c].dropna().astype(str).str.strip()
        n = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
        n_strict = pd.to_numeric(s, errors="coerce")
        if len(s) and n.notna().mean() >= 0.5:
            malos = s[n_strict.isna()]
            print(f"{nombre}.{c}: numérica · no convierten tal como llegan: {len(malos)}",
                  malos.value_counts().head(10).to_dict() if len(malos) else "")
            if n.notna().any():
                print(f"   mín {n.min()} · máx {n.max()} · negativos {int((n < 0).sum())}")

F = {c: a_fecha(o[c]) for c in fechas}
print()
for c in fechas:
    malos = o[c].notna() & F[c].isna()
    print(f"{c}: no convierten: {int(malos.sum())}", o.loc[malos, c].value_counts().head(10).to_dict())
    print(f"   después del corte ({CORTE.date()}): {int((F[c] > CORTE + pd.Timedelta(days=1)).sum())}"
          f" · antes de 2015: {int((F[c] < '2015-01-01').sum())}"
          f" · rango: {F[c].min()} a {F[c].max()}")


def buscar(palabra):
    return next((c for c in fechas if palabra in norm_txt(c)), None)


orden = [c for c in (buscar("solicitud"), buscar("atencion"), buscar("cierre")) if c]
print("\nOrden lógico de fechas:", " <= ".join(orden))
for a, b in zip(orden, orden[1:]):
    print(f"   {b} antes de {a}: {int((F[b] < F[a]).sum())}")
if len(orden) == 3:
    print(f"   {orden[2]} antes de {orden[0]}: {int((F[orden[2]] < F[orden[0]]).sum())}")
