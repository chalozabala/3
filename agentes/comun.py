# -*- coding: utf-8 -*-
"""Utilidades compartidas por los agentes: carga de tablas, parsers y escritura."""
import csv
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDAS = RAIZ / "agentes" / "salidas"

EMPRESAS_CSV = DATA / "bd_empresas.csv"
CONTACTOS_CSV = DATA / "bd_contactos.csv"
ACTIVIDADES_CSV = DATA / "bd_actividades.csv"
PROPUESTAS_CSV = DATA / "bd_propuestas.csv"


def cargar(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cargar_empresas():
    return cargar(EMPRESAS_CSV)


def cargar_contactos():
    return cargar(CONTACTOS_CSV)


def cargar_actividades():
    return cargar(ACTIVIDADES_CSV)


def cargar_propuestas():
    return cargar(PROPUESTAS_CSV)


def contactos_por_empresa(contactos=None):
    contactos = contactos if contactos is not None else cargar_contactos()
    por_emp = {}
    for c in contactos:
        por_emp.setdefault(c["ID_EMPRESA"], []).append(c)
    return por_emp


def norm(s):
    """MAYÚSCULAS sin acentos, para comparar texto libre."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.upper().strip()


def parse_fecha(s):
    """Acepta DD/MM/YYYY, DD/MM/YY y M/YY ('3/26' = 01/03/2026). None si no parsea."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.fullmatch(r"(\d{1,2})/(\d{2})", s)
    if m:
        mes, anio = int(m.group(1)), 2000 + int(m.group(2))
        if 1 <= mes <= 12:
            return date(anio, mes, 1)
    return None


def parse_tamano(s):
    """Dotación estimada: el mayor entero que aparezca ('100-200' -> 200, '+2000' -> 2000)."""
    nums = [int(n) for n in re.findall(r"\d+", (s or "").replace(".", ""))]
    return max(nums) if nums else 0


def es_si(v):
    return norm(v) in ("SI", "ACEPTADA", "ACEPTADO")


def slug(s, largo=40):
    s = norm(s).replace(" ", "-")
    s = re.sub(r"[^A-Z0-9\-]", "", s)
    return s[:largo].strip("-").lower() or "sin-nombre"


def proximo_id(filas, campo, prefijo):
    """Siguiente ID secuencial: proximo_id(actividades, 'ID_ACTIVIDAD', 'ACT') -> 'ACT-0002'."""
    mayor = 0
    for f in filas:
        m = re.fullmatch(rf"{prefijo}-(\d+)", (f.get(campo) or "").strip())
        if m:
            mayor = max(mayor, int(m.group(1)))
    return f"{prefijo}-{mayor + 1:04d}"


def append_fila(path, fila):
    """Agrega una fila (dict) respetando el encabezado existente del CSV."""
    with open(path, newline="", encoding="utf-8") as f:
        cols = next(csv.reader(f))
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=cols).writerow({c: fila.get(c, "") for c in cols})


def escribir_csv(path, filas, cols):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)


# ---- ranking de contactos -------------------------------------------------

AREAS_OBJETIVO = ("Compras", "RRHH")
SENIORITY_DECISOR = ("GERENTE", "JEFE", "DIRECTOR", "RESPONSABLE", "MANAGER", "COORDINADOR")


def puntaje_contacto(c):
    p = 0
    area = c.get("AREA", "")
    if area in AREAS_OBJETIVO:
        p += 40
    elif area == "Dirección/Dueño":
        p += 20
    elif area in ("Planta/Operaciones", "Administración/Finanzas"):
        p += 15
    else:
        p += 5
    conf = c.get("CONFIANZA", "")
    if conf.startswith("Alta"):
        p += 15
    elif conf.startswith("Media-Alta"):
        p += 10
    elif conf.startswith("Media"):
        p += 6
    if (c.get("EMAIL") or "").strip():
        p += 12
    if (c.get("LINKEDIN_FUENTE") or "").strip().startswith("http"):
        p += 8
    if any(s in norm(c.get("SENIORITY", "")) or s in norm(c.get("CARGO", "")) for s in SENIORITY_DECISOR):
        p += 5
    if c.get("VERIFICADO") == "SI":
        p += 10
    if "EX " in norm(c.get("NOTAS", "")) or "POSIBLE EX" in norm(c.get("NOTAS", "")):
        p -= 15
    return p


def contactos_rankeados(lista):
    return sorted(lista, key=puntaje_contacto, reverse=True)
