# -*- coding: utf-8 -*-
"""Agente priorizador: rankea las cuentas y arma la cola de trabajo comercial.

Uso:
    python3 agentes/priorizador.py                 # top 40 + resumen
    python3 agentes/priorizador.py --top 60
    python3 agentes/priorizador.py --todas         # todas las cuentas activas
    python3 agentes/priorizador.py --detalle EMP-0012
El CSV queda en agentes/salidas/cola_trabajo_<fecha>.csv
"""
import argparse
from datetime import date

from comun import (
    AREAS_OBJETIVO, SALIDAS, cargar_empresas, contactos_por_empresa,
    contactos_rankeados, es_si, escribir_csv, norm, parse_fecha, parse_tamano,
)

PIPELINE_ACTIVO = ("CONVERSACION", "PRESUPUESTO", "PRESENTACION", "REUNION",
                   "LICITA", "ENVIA", "ARRANCA", "COTIZ")


def motivo_exclusion(e):
    a = norm(e.get("ALERTA", ""))
    if a.startswith("CERRADA"):
        return "cerrada"
    if "DUPLICADO" in a or "MISMO GRUPO" in a or "CASI SEGURO = ACINDAR" in a:
        return "duplicado de otra cuenta"
    if a.startswith("NO IDENTIFICADA"):
        return "sin identificar (pedir CUIT/mail/tel)"
    return None


def evaluar(e, contactos):
    """Devuelve (score, motivos, mejor_contacto)."""
    puntos, motivos = 0, []
    ranked = contactos_rankeados(contactos)
    mejor = ranked[0] if ranked else None

    areas = {c["AREA"] for c in contactos}
    if areas & set(AREAS_OBJETIVO):
        puntos += 30
        motivos.append("contacto Compras/RRHH con nombre")
        if set(AREAS_OBJETIVO) <= areas:
            puntos += 10
            motivos.append("Compras y RRHH cubiertos")
    elif contactos:
        puntos += 12
        motivos.append("contacto nombrado (otra área)")

    if mejor:
        conf = mejor.get("CONFIANZA", "")
        if conf.startswith("Alta"):
            puntos += 12
        elif conf.startswith("Media-Alta"):
            puntos += 6
    if any((c.get("EMAIL") or "").strip() for c in contactos):
        puntos += 15
        motivos.append("mail directo confirmado")
    if mejor and (mejor.get("LINKEDIN_FUENTE") or "").startswith("http"):
        puntos += 8

    if (e.get("MAIL_GENERAL") or "").strip():
        puntos += 5
    if (e.get("TELEFONO_CEL") or "").strip():
        puntos += 5
    if (e.get("CONTACTO_HISTORICO") or "").strip():
        puntos += 6
        motivos.append(f"relación previa: {e['CONTACTO_HISTORICO'][:40]}")

    estado = norm(e.get("ESTADO_PIPELINE", ""))
    contactado, respuesta = es_si(e.get("CONTACTADO", "")), es_si(e.get("RESPUESTA", ""))
    if contactado and respuesta:
        puntos += 30
        motivos.append("respondió: conversación abierta")
    elif any(k in estado for k in PIPELINE_ACTIVO):
        puntos += 25
        motivos.append(f"pipeline activo: {e['ESTADO_PIPELINE'].strip()}")
    elif contactado:
        puntos += 5
        motivos.append("ya contactada, sin respuesta")

    volver = (e.get("FECHA_VOLVER_CONTACTAR") or "").strip()
    if volver:
        f = parse_fecha(volver)
        if f and f <= date.today():
            puntos += 20
            motivos.append(f"seguimiento vencido ({volver})")
        else:
            motivos.append(f"volver a contactar: {volver}")

    prioridad = (e.get("PRIORIDAD") or "").strip()
    puntos += {"1": 15, "2": 8, "3": 3}.get(prioridad, 0)
    if prioridad:
        motivos.append(f"prioridad {prioridad} del equipo")
    if es_si(e.get("LICITA", "")):
        puntos += 5
        motivos.append("licita")

    dot = parse_tamano(e.get("TAMANO_ESTIMADO", ""))
    if dot >= 1000:
        puntos += 20
    elif dot >= 400:
        puntos += 16
    elif dot >= 150:
        puntos += 12
    elif dot >= 50:
        puntos += 8
    elif dot > 0:
        puntos += 4
    if dot:
        motivos.append(f"dotación ~{dot}")

    if (e.get("TIPO_SERVICIO") or "").strip():
        puntos += 4
    if norm(e.get("ALERTA", "")).startswith(("VERIFICAR", "SITIO NO CONFIRMADO", "COMPRADA")):
        puntos -= 5
        motivos.append(f"ojo: {e['ALERTA'][:50]}")

    return puntos, motivos, mejor


def canal_sugerido(e, mejor):
    if mejor and (mejor.get("EMAIL") or "").strip():
        return "mail directo"
    if mejor and (mejor.get("LINKEDIN_FUENTE") or "").startswith("http"):
        return "LinkedIn (manual)"
    if (e.get("MAIL_GENERAL") or "").strip():
        return "mail institucional"
    if (e.get("TELEFONO_CEL") or "").strip():
        return "teléfono"
    return "—"


def accion_sugerida(e, mejor, motivos):
    m = " | ".join(motivos)
    quien = f"{mejor['NOMBRE']} ({mejor['CARGO'][:45]})" if mejor else ""
    if "conversación abierta" in m or "pipeline activo" in m:
        return f"Retomar: {e.get('ESTADO_PIPELINE', '').strip() or 'seguimiento de la conversación'}"
    if "seguimiento vencido" in m:
        return f"Reactivar contacto ({e.get('FECHA_VOLVER_CONTACTAR', '').strip()})"
    if mejor and (mejor.get("EMAIL") or "").strip():
        return f"Verificar cargo y mandar mail personalizado a {quien}"
    if mejor and (mejor.get("LINKEDIN_FUENTE") or "").startswith("http"):
        return f"Verificar en LinkedIn y contactar manualmente a {quien}"
    if mejor:
        return f"Buscar canal para {quien}"
    if (e.get("MAIL_GENERAL") or "").strip() or (e.get("TELEFONO_CEL") or "").strip():
        return "Llamar / escribir al canal institucional"
    return "Derivar al agente de enriquecimiento (sin contacto ni canal)"


def armar_cola():
    empresas = cargar_empresas()
    por_emp = contactos_por_empresa()
    activas, excluidas = [], []
    for e in empresas:
        razon = motivo_exclusion(e)
        if razon:
            excluidas.append((e, razon))
            continue
        contactos = por_emp.get(e["ID_EMPRESA"], [])
        score, motivos, mejor = evaluar(e, contactos)
        activas.append({
            "ID_EMPRESA": e["ID_EMPRESA"],
            "EMPRESA": e["EMPRESA"],
            "LOCALIDAD": e.get("LOCALIDAD", ""),
            "SCORE": score,
            "MEJOR_CONTACTO": f"{mejor['NOMBRE']} — {mejor['CARGO']}"[:90] if mejor else "",
            "AREA_CONTACTO": mejor["AREA"] if mejor else "",
            "CANAL_SUGERIDO": canal_sugerido(e, mejor),
            "ACCION_SUGERIDA": accion_sugerida(e, mejor, motivos),
            "MOTIVOS": " | ".join(motivos),
            "ALERTA": e.get("ALERTA", ""),
        })
    activas.sort(key=lambda r: r["SCORE"], reverse=True)
    for i, r in enumerate(activas, 1):
        r["RANKING"] = i
    return activas, excluidas


def main():
    ap = argparse.ArgumentParser(description="Arma la cola de trabajo priorizada.")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--detalle", metavar="EMP-XXXX")
    args = ap.parse_args()

    if args.detalle:
        detalle(args.detalle)
        return

    activas, excluidas = armar_cola()
    corte = activas if args.todas else activas[: args.top]

    cols = ["RANKING", "ID_EMPRESA", "EMPRESA", "LOCALIDAD", "SCORE", "MEJOR_CONTACTO",
            "AREA_CONTACTO", "CANAL_SUGERIDO", "ACCION_SUGERIDA", "MOTIVOS", "ALERTA"]
    salida = SALIDAS / f"cola_trabajo_{date.today().isoformat()}.csv"
    escribir_csv(salida, corte, cols)

    print(f"Cuentas activas: {len(activas)}  |  excluidas: {len(excluidas)}")
    from collections import Counter
    for razon, n in Counter(r for _, r in excluidas).items():
        print(f"  - {razon}: {n}")
    print(f"\nCola escrita en {salida}  ({len(corte)} cuentas)\n")
    for r in corte[:15]:
        print(f"{r['RANKING']:3d}. [{r['SCORE']:3d}] {r['EMPRESA'][:42]:42s} {r['CANAL_SUGERIDO']:18s} {r['ACCION_SUGERIDA'][:60]}")


def detalle(id_emp):
    e = next((x for x in cargar_empresas() if x["ID_EMPRESA"] == id_emp), None)
    if not e:
        print(f"No existe {id_emp}")
        return
    contactos = contactos_por_empresa().get(id_emp, [])
    score, motivos, _ = evaluar(e, contactos)
    print(f"{e['ID_EMPRESA']} — {e['EMPRESA']}  [score {score}]")
    for k in ("LOCALIDAD", "ESTADO_PIPELINE", "PROVEEDOR_ACTUAL", "TAMANO_ESTIMADO",
              "MAIL_GENERAL", "TELEFONO_CEL", "CONTACTO_HISTORICO", "ALERTA",
              "OBSERVACIONES_RELEVAMIENTO"):
        if (e.get(k) or "").strip():
            print(f"  {k}: {e[k]}")
    print(f"  MOTIVOS: {' | '.join(motivos)}")
    print(f"  Contactos ({len(contactos)}):")
    for c in contactos_rankeados(contactos):
        extra = " ".join(filter(None, [c.get("EMAIL"), c.get("LINKEDIN_FUENTE")]))
        print(f"   - {c['ID_CONTACTO']} {c['NOMBRE']} | {c['CARGO'][:50]} | {c['AREA']} | conf {c['CONFIANZA']} | {extra[:70]}")


if __name__ == "__main__":
    main()
