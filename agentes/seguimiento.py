# -*- coding: utf-8 -*-
"""Agente de seguimiento: detecta vencimientos y arma la lista de 'hoy toca'.

Lee bd_actividades (actividades abiertas con FECHA_PROXIMO vencida o por vencer)
y bd_empresas (FECHA_VOLVER_CONTACTAR). No modifica nada: informa.

Uso:
    python3 agentes/seguimiento.py            # vencidos + próximos 7 días
    python3 agentes/seguimiento.py --dias 14
"""
import argparse
from datetime import date, timedelta

from comun import cargar_actividades, cargar_empresas, parse_fecha


def main():
    ap = argparse.ArgumentParser(description="Vencimientos de seguimiento.")
    ap.add_argument("--dias", type=int, default=7, help="horizonte hacia adelante")
    args = ap.parse_args()
    hoy = date.today()
    limite = hoy + timedelta(days=args.dias)
    empresas = {e["ID_EMPRESA"]: e for e in cargar_empresas()}

    print(f"=== Seguimientos (hoy {hoy.isoformat()}, horizonte {args.dias} días) ===\n")

    abiertas = [a for a in cargar_actividades() if (a.get("ESTADO") or "").strip() == "abierta"]
    vencidas, proximas, sin_fecha = [], [], []
    for a in abiertas:
        f = parse_fecha(a.get("FECHA_PROXIMO", ""))
        if f is None:
            sin_fecha.append(a)
        elif f <= hoy:
            vencidas.append((f, a))
        elif f <= limite:
            proximas.append((f, a))

    def linea(a):
        emp = empresas.get(a.get("ID_EMPRESA", ""), {}).get("EMPRESA", a.get("ID_EMPRESA", "?"))
        return (f"  {a['ID_ACTIVIDAD']} · {emp[:35]:35s} · {a.get('TIPO', ''):9s} · "
                f"{a.get('PROXIMO_PASO', '')[:45]}")

    print(f"-- Actividades VENCIDAS ({len(vencidas)}) --")
    for f, a in sorted(vencidas):
        print(f"  [{f.isoformat()}]" + linea(a))
    print(f"\n-- Próximos {args.dias} días ({len(proximas)}) --")
    for f, a in sorted(proximas):
        print(f"  [{f.isoformat()}]" + linea(a))
    if sin_fecha:
        print(f"\n-- Abiertas sin FECHA_PROXIMO ({len(sin_fecha)}): ponerles fecha --")
        for a in sin_fecha:
            print(linea(a))

    pendientes = []
    for e in cargar_empresas():
        raw = (e.get("FECHA_VOLVER_CONTACTAR") or "").strip()
        if not raw:
            continue
        f = parse_fecha(raw)
        if f is None or f <= limite:
            pendientes.append((f, raw, e))
    print(f"\n-- Empresas con 'volver a contactar' vencido o próximo ({len(pendientes)}) --")
    for f, raw, e in sorted(pendientes, key=lambda x: (x[0] is None, x[0] or hoy)):
        print(f"  [{raw:8s}] {e['ID_EMPRESA']} · {e['EMPRESA'][:40]:40s} · {e.get('ESTADO_PIPELINE', '')[:30]}")

    if not (vencidas or proximas or sin_fecha or pendientes):
        print("Nada vencido ni próximo. La cola nueva la arma el priorizador.")


if __name__ == "__main__":
    main()
