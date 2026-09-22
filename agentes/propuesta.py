# -*- coding: utf-8 -*-
"""Agente de propuesta: genera el borrador de propuesta comercial de una cuenta.

Uso:
    python3 agentes/propuesta.py --empresa EMP-0316
    python3 agentes/propuesta.py --empresa "boero" --tipo comedor --personas 120
    python3 agentes/propuesta.py --empresa EMP-0316 --registrar   # además la anota en bd_propuestas
    python3 agentes/propuesta.py --empresa EMP-0316 --ia          # pule la redacción con Claude

El borrador queda en agentes/salidas/propuestas/ y SIEMPRE lo revisa una persona
(los [COMPLETAR: ...] son datos del negocio que el agente no debe inventar).
"""
import argparse
from datetime import date
from pathlib import Path

from comun import (
    PROPUESTAS_CSV, SALIDAS, append_fila, cargar_empresas, cargar_propuestas,
    contactos_por_empresa, contactos_rankeados, norm, parse_tamano, proximo_id, slug,
)

PLANTILLA = Path(__file__).parent / "plantillas" / "propuesta_base.md"

BLOQUE_COMEDOR = (
    "Montamos y operamos el comedor dentro de la planta: personal gastronómico "
    "propio, equipamiento de regeneración y servido, y administración de "
    "comensales por turno. La empresa aporta el espacio; nosotros nos ocupamos "
    "del resto (menú, elaboración, servido, limpieza del sector y reposición)."
)
BLOQUE_VIANDAS = (
    "Elaboramos las viandas en nuestra planta habilitada y las entregamos "
    "rotuladas de manera individual, en frío o listas para regenerar, con "
    "cadena de frío controlada y planillas de entrega por turno. Es la opción "
    "más simple cuando la planta no tiene cocina propia: sin obra, sin "
    "personal extra y con consumo facturado por vianda efectivamente pedida."
)


def zona_referencia(localidad):
    l = norm(localidad)
    if any(k in l for k in ("SAN LORENZO", "PUERTO", "TIMBUES", "RICARDONE", "ALDAO")):
        return "San Lorenzo – Puerto Gral. San Martín – Timbúes"
    if any(k in l for k in ("SAN NICOLAS", "RAMALLO")):
        return "San Nicolás – Ramallo"
    return "Gran Rosario"


def buscar_empresa(clave):
    empresas = cargar_empresas()
    clave_n = norm(clave)
    exacta = next((e for e in empresas if e["ID_EMPRESA"] == clave.strip().upper()), None)
    if exacta:
        return exacta
    candidatas = [e for e in empresas if clave_n in norm(e["EMPRESA"])]
    if len(candidatas) == 1:
        return candidatas[0]
    if not candidatas:
        raise SystemExit(f"No encontré ninguna empresa que matchee '{clave}'.")
    lista = ", ".join(f"{e['ID_EMPRESA']} {e['EMPRESA']}" for e in candidatas[:8])
    raise SystemExit(f"'{clave}' es ambiguo: {lista}. Usá el ID_EMPRESA.")


def generar(e, tipo=None, personas=None, turnos=None, usar_ia=False, registrar=False):
    contactos = contactos_rankeados(contactos_por_empresa().get(e["ID_EMPRESA"], []))
    mejor = contactos[0] if contactos else None

    tipo_campo = norm(tipo or e.get("TIPO_SERVICIO", ""))
    es_comedor = "COMEDOR" in tipo_campo
    tipo_largo = "comedor in-company" if es_comedor else "viandas"

    dot = personas or parse_tamano(e.get("TAMANO_ESTIMADO", ""))
    contexto_partes = [e.get(k, "").strip() for k in
                       ("OBSERVACIONES_RELEVAMIENTO", "COMENTARIOS_PROPIOS") if e.get(k, "").strip()]
    if e.get("PROVEEDOR_ACTUAL", "").strip():
        contexto_partes.append(f"proveedor actual relevado: {e['PROVEEDOR_ACTUAL'].strip()}")

    id_prop = proximo_id(cargar_propuestas(), "ID_PROPUESTA", "PROP")
    valores = {
        "EMPRESA": e["EMPRESA"],
        "LOCALIDAD": e.get("LOCALIDAD", "").strip() or "[COMPLETAR: localidad]",
        "DESTINATARIO": (f"{mejor['NOMBRE']} — {mejor['CARGO']}" if mejor
                         else "Sector Compras / Recursos Humanos"),
        "FECHA": date.today().strftime("%d/%m/%Y"),
        "ID_PROPUESTA": id_prop,
        "TIPO_SERVICIO_LARGO": tipo_largo,
        "DOTACION": str(dot) if dot else "[COMPLETAR: dotación]",
        "TURNOS": turnos or "[COMPLETAR: turnos y horarios]",
        "CONTEXTO": " / ".join(contexto_partes)[:400] or "[COMPLETAR: contexto relevado]",
        "BLOQUE_MODALIDAD": BLOQUE_COMEDOR if es_comedor else BLOQUE_VIANDAS,
        "FIRMA": "[TU NOMBRE]\n[TU EMPRESA] — [TELÉFONO] — [MAIL]",
    }
    texto = PLANTILLA.read_text(encoding="utf-8")
    for k, v in valores.items():
        texto = texto.replace("{{" + k + "}}", v)

    encabezado = (
        f"> **BORRADOR generado por el agente de propuesta — {date.today().isoformat()}**\n"
        f"> Cuenta: {e['ID_EMPRESA']} {e['EMPRESA']} · Revisar los [COMPLETAR] y validar\n"
        f"> los datos relevados antes de enviar. Nada se envía sin aprobación humana.\n\n"
    )
    texto = encabezado + texto

    if usar_ia:
        from ia import pulir
        texto = pulir(texto, " / ".join(contexto_partes) or "sin contexto adicional")

    destino = SALIDAS / "propuestas" / f"{date.today().isoformat()}_{id_prop}_{slug(e['EMPRESA'])}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    print(f"Borrador escrito en {destino}")

    if registrar:
        append_fila(PROPUESTAS_CSV, {
            "ID_PROPUESTA": id_prop,
            "ID_EMPRESA": e["ID_EMPRESA"],
            "FECHA": date.today().isoformat(),
            "TIPO_SERVICIO": tipo_largo,
            "CANT_PERSONAS_ESTIMADA": str(dot) if dot else "",
            "TURNOS": turnos or "",
            "ESTADO": "borrador",
            "LINK_DOCUMENTO": str(destino.relative_to(SALIDAS.parent.parent)),
            "NOTAS": "generada por agente de propuesta; pendiente de revisión humana",
        })
        print(f"Registrada como {id_prop} (estado: borrador) en bd_propuestas.csv")
    return destino


def main():
    ap = argparse.ArgumentParser(description="Genera el borrador de propuesta de una cuenta.")
    ap.add_argument("--empresa", required=True, help="ID_EMPRESA o parte del nombre")
    ap.add_argument("--tipo", choices=["comedor", "viandas"])
    ap.add_argument("--personas", type=int)
    ap.add_argument("--turnos")
    ap.add_argument("--ia", action="store_true", help="pulir redacción con la API de Claude")
    ap.add_argument("--registrar", action="store_true", help="anotar la propuesta en bd_propuestas.csv")
    args = ap.parse_args()
    e = buscar_empresa(args.empresa)
    generar(e, args.tipo, args.personas, args.turnos, args.ia, args.registrar)


if __name__ == "__main__":
    main()
