# -*- coding: utf-8 -*-
"""Genera aplicativo/datos.js (los maestros que consume la app publicada).

Correr después de cada actualización de data/: python3 aplicativo/build_datos.py
Luego republicar el artifact con el datos.js nuevo.
"""
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "agentes"))

from comun import cargar_contactos, cargar_propuestas  # noqa: E402
from priorizador import armar_cola, motivo_exclusion  # noqa: E402
from comun import cargar_empresas  # noqa: E402


def main():
    activas, excluidas = armar_cola()
    por_id = {r["ID_EMPRESA"]: r for r in activas}
    razon_exc = {e["ID_EMPRESA"]: razon for e, razon in excluidas}

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
