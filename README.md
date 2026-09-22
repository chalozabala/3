# Base de datos comercial — Servicio de comedor/viandas Gran Rosario

Base de datos de prospección para armar la fuerza de venta y los agentes de IA
(propuesta, contacto, seguimiento) del servicio de comedor y viandas en el cordón
industrial Gran Rosario – San Lorenzo – Puerto Gral. San Martín – Timbúes – San Nicolás.

## Estructura

```
data/
  bd_empresas.csv      376 cuentas (1 fila por empresa)  — clave: ID_EMPRESA
  bd_contactos.csv     314 personas (1 fila por contacto) — clave: ID_CONTACTO → ID_EMPRESA
  bd_actividades.csv   bitácora de interacciones (la llenan vendedores/agentes)
  bd_propuestas.csv    registro de propuestas por cuenta (PROP-0001/0002: borradores de ejemplo)
  fuentes/             datos crudos: hoja original + relevamientos 21/22-09-2026
agentes/
  priorizador.py       arma la cola de trabajo priorizada     → salidas/cola_trabajo_*.csv
  propuesta.py         borrador de propuesta por cuenta       → salidas/propuestas/
  contacto.py          borradores de mail + LinkedIn          → salidas/borradores/
  seguimiento.py       vencimientos de actividades y cuentas
  plantillas/          plantillas de propuesta y mensajes
  README.md            manual de operación y ciclo semanal
docs/
  diccionario_datos.md diccionario de columnas y reglas de uso
  aplicativo_appsheet.md cómo montar la app (AppSheet/Glide) sobre las planillas
```

## Modelo relacional

`EMPRESAS 1—N CONTACTOS` · `EMPRESAS 1—N ACTIVIDADES` · `CONTACTOS 1—N ACTIVIDADES` · `EMPRESAS 1—N PROPUESTAS`

Toda escritura de los agentes va a **ACTIVIDADES** y **PROPUESTAS**; EMPRESAS y
CONTACTOS solo se actualizan al verificar o enriquecer datos (campo `VERIFICADO`,
`ESTADO_CONTACTO`, `ESTADO_PIPELINE`).

## Agentes (implementados en `agentes/`)

1. **Priorizador** (`priorizador.py`): rankea las cuentas por pipeline activo,
   decisor identificado, canal disponible, dotación y prioridad del equipo;
   arma la cola de trabajo (`--top`, `--todas`, `--detalle EMP-XXXX`).
2. **Propuesta** (`propuesta.py`): genera el borrador de propuesta por cuenta
   (comedor o viandas) y con `--registrar` lo anota en PROPUESTAS.
3. **Contacto** (`contacto.py`): redacta mail + mensaje de LinkedIn por
   contacto. **El envío lo hace y aprueba una persona**; después se registra
   con `--registrar-envio`, que también pasa el contacto a `contactado`.
4. **Seguimiento** (`seguimiento.py`): lee ACTIVIDADES y EMPRESAS y lista lo
   vencido y lo próximo.
5. **Enriquecimiento**: sin script — investigación con sesiones de Claude que
   actualizan los maestros con fuentes citadas (ver `agentes/README.md`).

Los cuatro scripts corren con Python 3 puro; `--ia` (opcional) pule la
redacción con la API de Claude si hay `ANTHROPIC_API_KEY` configurada.
Manual completo: `agentes/README.md`.

## Reglas de uso (importantes)

- **Verificar antes de contactar**: los contactos provienen de fuentes públicas
  (snippets de buscador, ZoomInfo/RocketReach, webs oficiales, Boletín Oficial).
  `CONFIANZA` + `VERIFICADO=NO` indican que el cargo puede estar desactualizado.
- **LinkedIn**: los perfiles se contactan manualmente desde la cuenta propia.
  No automatizar acciones dentro de LinkedIn (viola sus términos de uso).
- **Mails**: envíos personalizados, de a poco y con revisión humana; nada de
  envíos masivos indiscriminados.
- La columna DIRECCIÓN de la hoja original venía desfasada respecto de la empresa
  y fue excluida del maestro; las direcciones verificadas están en
  `OBSERVACIONES_RELEVAMIENTO` y en `data/fuentes/`.
