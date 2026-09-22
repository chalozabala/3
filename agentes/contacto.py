# -*- coding: utf-8 -*-
"""Agente de contacto (drafting): redacta borradores de mail y mensaje de LinkedIn
personalizados por contacto. NUNCA envía nada: el envío es manual, con revisión
y aprobación de una persona, y LinkedIn se usa siempre a mano desde la cuenta propia.

Uso:
    python3 agentes/contacto.py --contacto CON-0123
    python3 agentes/contacto.py --empresa EMP-0316            # mejor contacto de la cuenta
    python3 agentes/contacto.py --empresa EMP-0316 --n 2      # los 2 mejores
    python3 agentes/contacto.py --contacto CON-0123 --ia      # pule la redacción con Claude
    python3 agentes/contacto.py --contacto CON-0123 --registrar-envio email
        # SOLO después de que la persona envió el mensaje: anota la actividad
        # en bd_actividades y pasa el contacto a 'contactado'.
"""
import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

from comun import (
    ACTIVIDADES_CSV, CONTACTOS_CSV, SALIDAS, append_fila, cargar_actividades,
    cargar_contactos, cargar_empresas, contactos_por_empresa, contactos_rankeados,
    proximo_id, slug,
)
from propuesta import zona_referencia

PLANTILLAS = Path(__file__).parent / "plantillas"


def plantilla_para(contacto):
    if contacto and contacto.get("AREA") == "RRHH":
        return PLANTILLAS / "mail_rrhh.md"
    if contacto:
        return PLANTILLAS / "mail_compras.md"
    return PLANTILLAS / "mail_general.md"


def sugerir_gancho(e, c):
    opciones = []
    prov = (e.get("PROVEEDOR_ACTUAL") or "").strip()
    if prov:
        opciones.append(
            f"Entendemos que hoy resuelven el servicio con {prov}; si están revisando "
            f"calidad o costos, es un buen momento para comparar."
        )
    if (e.get("CONTACTO_HISTORICO") or "").strip():
        opciones.append(
            f"Hace un tiempo estuvimos en contacto con gente de {e['EMPRESA']} "
            f"({e['CONTACTO_HISTORICO'].strip()[:50]}); retomo por este canal."
        )
    notas = (c.get("NOTAS") or "").strip() if c else ""
    obs = (e.get("OBSERVACIONES_RELEVAMIENTO") or "").strip()
    dato = notas or obs
    if dato:
        opciones.append(f"[dato relevado para personalizar: {dato[:160]}]")
    if not opciones:
        return "[GANCHO: personalizar con un dato de la planta — obra, turno nuevo, búsqueda activa, etc.]"
    listado = "\n".join(f">   {i}. {o}" for i, o in enumerate(opciones, 1))
    return ("[GANCHO — elegir/ajustar UNA de estas líneas y borrar el resto:]\n" + listado)


def generar(c, e, usar_ia=False):
    nombre_pila = (c["NOMBRE"].split() or ["Estimado/a"])[0] if c else ""
    valores = {
        "EMPRESA": e["EMPRESA"],
        "NOMBRE_PILA": nombre_pila,
        "ZONA_REFERENCIA": zona_referencia(e.get("LOCALIDAD", "")),
        "GANCHO": sugerir_gancho(e, c),
    }

    mail = plantilla_para(c).read_text(encoding="utf-8")
    linkedin = (PLANTILLAS / "mensaje_linkedin.md").read_text(encoding="utf-8")
    for k, v in valores.items():
        mail = mail.replace("{{" + k + "}}", v)
        linkedin = linkedin.replace("{{" + k + "}}", v)

    datos = "\n".join(filter(None, [
        f"> **Contacto:** {c['ID_CONTACTO']} — {c['NOMBRE']} · {c['CARGO']} · área {c['AREA']}" if c else
        f"> **Contacto:** canal institucional ({e.get('MAIL_GENERAL', '') or e.get('TELEFONO_CEL', '')})",
        f"> **Mail:** {c['EMAIL']}" if c and c.get("EMAIL", "").strip() else None,
        f"> **LinkedIn:** {c['LINKEDIN_FUENTE']}" if c and c.get("LINKEDIN_FUENTE", "").startswith("http") else None,
        f"> **Confianza del dato:** {c['CONFIANZA']} · VERIFICADO={c['VERIFICADO']}" if c else None,
        f"> **Notas del relevamiento:** {c['NOTAS'][:150]}" if c and c.get("NOTAS", "").strip() else None,
    ]))
    encabezado = (
        f"> **BORRADOR — NO ENVIAR SIN APROBACIÓN HUMANA** · generado {date.today().isoformat()}\n"
        f"> Antes de enviar: 1) verificar el cargo en LinkedIn desde tu cuenta, "
        f"2) completar los [corchetes], 3) marcar VERIFICADO=SI en bd_contactos.\n"
        f"> LinkedIn se contacta SIEMPRE a mano desde la cuenta propia (nada automatizado).\n"
        + datos + "\n\n---\n\n"
    )

    cuerpo = encabezado + "## Mail\n\n" + mail + "\n\n---\n\n## LinkedIn\n\n" + linkedin
    if usar_ia:
        from ia import pulir
        contexto = f"{e['EMPRESA']} ({e.get('LOCALIDAD', '')}). " \
                   f"Obs: {e.get('OBSERVACIONES_RELEVAMIENTO', '')[:200]}"
        cuerpo = pulir(cuerpo, contexto)

    quien = c["ID_CONTACTO"] if c else "canal-general"
    destino = SALIDAS / "borradores" / f"{date.today().isoformat()}_{quien}_{slug(e['EMPRESA'])}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(cuerpo, encoding="utf-8")
    print(f"Borrador escrito en {destino}")
    return destino


def registrar_envio(c, e, tipo):
    """Se llama SOLO cuando la persona ya envió el mensaje: deja registro del hecho."""
    id_act = proximo_id(cargar_actividades(), "ID_ACTIVIDAD", "ACT")
    append_fila(ACTIVIDADES_CSV, {
        "ID_ACTIVIDAD": id_act,
        "FECHA": date.today().isoformat(),
        "ID_EMPRESA": e["ID_EMPRESA"],
        "ID_CONTACTO": c["ID_CONTACTO"] if c else "",
        "RESPONSABLE_AGENTE": "agente-contacto (envío manual aprobado)",
        "TIPO": tipo,
        "DIRECCION": "saliente",
        "RESUMEN": f"Primer contacto {tipo} a {c['NOMBRE'] if c else 'canal institucional'}",
        "RESULTADO": "enviado",
        "PROXIMO_PASO": "seguimiento si no responde",
        "FECHA_PROXIMO": (date.today() + timedelta(days=7)).isoformat(),
        "ESTADO": "abierta",
    })
    if c:
        filas = cargar_contactos()
        for f in filas:
            if f["ID_CONTACTO"] == c["ID_CONTACTO"]:
                f["ESTADO_CONTACTO"] = "contactado"
        with open(CONTACTOS_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
    print(f"Registrado {id_act} ({tipo}, saliente) y contacto marcado 'contactado'.")


def main():
    ap = argparse.ArgumentParser(description="Redacta borradores de contacto (mail + LinkedIn).")
    ap.add_argument("--contacto", metavar="CON-XXXX")
    ap.add_argument("--empresa", metavar="EMP-XXXX")
    ap.add_argument("--n", type=int, default=1, help="con --empresa: cuántos contactos")
    ap.add_argument("--ia", action="store_true")
    ap.add_argument("--registrar-envio", choices=["email", "linkedin", "llamada", "whatsapp"],
                    help="anota en bd_actividades un envío YA HECHO por una persona")
    args = ap.parse_args()

    empresas = {e["ID_EMPRESA"]: e for e in cargar_empresas()}
    if args.contacto:
        c = next((x for x in cargar_contactos() if x["ID_CONTACTO"] == args.contacto.upper()), None)
        if not c:
            raise SystemExit(f"No existe {args.contacto}")
        pares = [(c, empresas[c["ID_EMPRESA"]])]
    elif args.empresa:
        e = empresas.get(args.empresa.upper())
        if not e:
            raise SystemExit(f"No existe {args.empresa}")
        ranked = contactos_rankeados(contactos_por_empresa().get(e["ID_EMPRESA"], []))
        pares = [(c, e) for c in ranked[: args.n]] or [(None, e)]
    else:
        raise SystemExit("Indicá --contacto CON-XXXX o --empresa EMP-XXXX")

    for c, e in pares:
        if args.registrar_envio:
            registrar_envio(c, e, args.registrar_envio)
        else:
            generar(c, e, args.ia)


if __name__ == "__main__":
    main()
