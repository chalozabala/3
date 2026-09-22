# -*- coding: utf-8 -*-
"""Genera aplicativo/datos.js (los maestros que consume la app publicada).

Correr después de cada actualización de data/: python3 aplicativo/build_datos.py
Luego republicar el artifact con el datos.js nuevo.
"""
import difflib
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "agentes"))

from comun import cargar_contactos, cargar_propuestas  # noqa: E402
from priorizador import armar_cola, motivo_exclusion  # noqa: E402
from comun import cargar_empresas  # noqa: E402

# ---- chequeo de destinatarios de mail (dominio vs. nombre de la cuenta) ----

GENERICOS = {"gmail", "hotmail", "yahoo", "outlook", "live", "icloud",
             "speedy", "arnet", "fibertel", "ciudad", "uolsinectis"}
STOP = {"SA", "SRL", "SAS", "SACIF", "SAIC", "DE", "DEL", "LA", "EL", "LOS",
        "LAS", "Y", "GRUPO", "ARGENTINA", "PLANTA", "CIA", "THE", "AND",
        "SERVICIOS", "SERVICE", "CONSTRUCCIONES", "CONSTRUCTORA"}


def _norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9 ]", " ", s.upper())


def _coincide(nombre, mail):
    local, dominio = mail.lower().split("@", 1)
    raiz = dominio.split(".")[0]
    palabras = _norm(nombre).split()
    tokens = [t for t in palabras if len(t) >= 3 and t not in STOP]
    junto = _norm(nombre).replace(" ", "").lower()
    sigla = "".join(w[0] for w in palabras if w and w not in STOP).lower()
    candidatos = [raiz, re.sub(r"[^a-z0-9]", "", local)]
    for cand in candidatos:
        if not cand:
            continue
        if cand in junto or junto[:6] and junto[:6] in cand:
            return True
        if len(sigla) >= 2 and (cand.startswith(sigla) or sigla in cand):
            return True
        for t in tokens:
            tl = t.lower()
            if tl in cand or cand in tl or tl[:4] == cand[:4]:
                return True
            if difflib.SequenceMatcher(None, tl, cand).ratio() >= 0.75:
                return True
    return False


def chequear_mails(empresas, mail_contacto):
    """Devuelve {ID_EMPRESA: (chk, motivo, dest)} con chk ok|gen|rev."""
    destinos, conteo = {}, {}
    for e in empresas:
        dest = mail_contacto.get(e["ID_EMPRESA"])
        origen = "contacto" if dest else "institucional"
        if not dest:
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", e.get("MAIL_GENERAL", ""))
            dest = m.group(0) if m else None
        if dest:
            destinos[e["ID_EMPRESA"]] = (dest, origen)
            conteo[dest.lower()] = conteo.get(dest.lower(), 0) + 1
    salida = {}
    for e in empresas:
        par = destinos.get(e["ID_EMPRESA"])
        if not par:
            continue
        dest, origen = par
        raiz = dest.split("@")[1].split(".")[0].lower()
        if conteo[dest.lower()] > 1:
            salida[e["ID_EMPRESA"]] = ("rev", f"misma casilla en {conteo[dest.lower()]} cuentas (mandar una sola vez)", dest)
        elif origen == "contacto":
            salida[e["ID_EMPRESA"]] = ("ok", "mail de contacto confirmado", dest)
        elif raiz in GENERICOS:
            salida[e["ID_EMPRESA"]] = ("gen", "casilla " + raiz + " (no verificable por dominio)", dest)
        elif _coincide(e["EMPRESA"], dest):
            salida[e["ID_EMPRESA"]] = ("ok", "dominio coincide con la cuenta", dest)
        else:
            salida[e["ID_EMPRESA"]] = ("rev", "el dominio no coincide con el nombre: verificar", dest)
    return salida


def main():
    activas, excluidas = armar_cola()
    por_id = {r["ID_EMPRESA"]: r for r in activas}
    razon_exc = {e["ID_EMPRESA"]: razon for e, razon in excluidas}

    contactos_crudos = cargar_contactos()
    mail_contacto = {}
    for c in contactos_crudos:
        if c["EMAIL"].strip() and not re.match(r"^EX[\s\-]", c["CARGO"].strip(), re.I):
            mail_contacto.setdefault(c["ID_EMPRESA"], c["EMAIL"].strip())
    chequeos = chequear_mails(cargar_empresas(), mail_contacto)

    empresas = []
    for e in cargar_empresas():
        r = por_id.get(e["ID_EMPRESA"], {})
        empresas.append({
            "id": e["ID_EMPRESA"],
            "nombre": e["EMPRESA"],
            "localidad": e.get("LOCALIDAD", ""),
            "prioridad": e.get("PRIORIDAD", ""),
            "estado_hoja": e.get("ESTADO_PIPELINE", ""),
            "contactado": e.get("CONTACTADO", ""),
            "respuesta": e.get("RESPUESTA", ""),
            "licita": e.get("LICITA", ""),
            "tipo": e.get("TIPO_SERVICIO", ""),
            "proveedor": e.get("PROVEEDOR_ACTUAL", ""),
            "f_ult": e.get("FECHA_ULT_CONTACTO", ""),
            "f_volver": e.get("FECHA_VOLVER_CONTACTAR", ""),
            "mail": e.get("MAIL_GENERAL", ""),
            "tel": e.get("TELEFONO_CEL", ""),
            "hist": e.get("CONTACTO_HISTORICO", ""),
            "tam": e.get("TAMANO_ESTIMADO", ""),
            "alerta": e.get("ALERTA", ""),
            "coment": e.get("COMENTARIOS_PROPIOS", ""),
            "obs": e.get("OBSERVACIONES_RELEVAMIENTO", ""),
            "score": r.get("SCORE", 0),
            "accion": r.get("ACCION_SUGERIDA", ""),
            "canal": r.get("CANAL_SUGERIDO", ""),
            "motivos": r.get("MOTIVOS", ""),
            "excluida": razon_exc.get(e["ID_EMPRESA"], ""),
            "chk": chequeos.get(e["ID_EMPRESA"], ("", "", ""))[0],
            "chk_motivo": chequeos.get(e["ID_EMPRESA"], ("", "", ""))[1],
            "chk_dest": chequeos.get(e["ID_EMPRESA"], ("", "", ""))[2],
        })

    contactos = [{
        "id": c["ID_CONTACTO"],
        "emp": c["ID_EMPRESA"],
        "nombre": c["NOMBRE"],
        "cargo": c["CARGO"],
        "area": c["AREA"],
        "linkedin": c.get("LINKEDIN_FUENTE", ""),
        "email": c.get("EMAIL", ""),
        "conf": c.get("CONFIANZA", ""),
        "verif": c.get("VERIFICADO", "NO"),
        "notas": c.get("NOTAS", ""),
    } for c in cargar_contactos()]

    propuestas = [{
        "id": p["ID_PROPUESTA"],
        "emp": p["ID_EMPRESA"],
        "fecha": p["FECHA"],
        "tipo": p["TIPO_SERVICIO"],
        "estado": p["ESTADO"],
        "notas": p.get("NOTAS", ""),
    } for p in cargar_propuestas()]

    datos = {
        "generado": date.today().isoformat(),
        "empresas": empresas,
        "contactos": contactos,
        "propuestas": propuestas,
    }
    js = "window.DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
    destino = RAIZ / "aplicativo" / "datos.js"
    destino.write_text(js, encoding="utf-8")
    print(f"{destino}  ({len(js) // 1024} KB, {len(empresas)} empresas, {len(contactos)} contactos)")


if __name__ == "__main__":
    main()
