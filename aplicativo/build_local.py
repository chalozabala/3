# -*- coding: utf-8 -*-
"""Empaqueta la app en UN solo archivo (Recorrida.html) que se abre con doble
clic en cualquier computadora, sin internet ni login. Los registros quedan en
el navegador de esa máquina (modo local).

Correr después de build_datos.py:  python3 aplicativo/build_local.py
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
html = (AQUI / "index.html").read_text(encoding="utf-8")
datos = (AQUI / "datos.js").read_text(encoding="utf-8")

marcador = '<script src="datos.js"></script>'
assert marcador in html, "no encuentro el tag de datos.js"
html = html.replace(marcador, "<script>\n" + datos + "</script>")

completo = (
    '<!doctype html>\n<html lang="es">\n<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    "</head>\n<body>\n" + html + "\n</body>\n</html>\n"
)
destino = AQUI / "Recorrida.html"
destino.write_text(completo, encoding="utf-8")
print(f"{destino}  ({len(completo) // 1024} KB)")
