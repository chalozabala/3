# Montar el aplicativo sin código (AppSheet / Glide)

Las 4 planillas de Drive ya están listas para usarse como backend de una app
móvil para la fuerza de venta. La opción recomendada es **AppSheet** (Google,
gratis hasta 10 usuarios en modo prototipo, se conecta directo a Sheets).

## Opción A — AppSheet (recomendada)

1. Entrar a [appsheet.com](https://www.appsheet.com) con la misma cuenta de
   Google del Drive → **Create → App → Start with existing data**.
2. Elegir **Google Sheets** y seleccionar la planilla **BD 1 — EMPRESAS**.
3. En **Data → Tables → Add Table**, sumar las otras tres planillas:
   BD 2 — CONTACTOS, BD 3 — ACTIVIDADES, BD 4 — PROPUESTAS.
   (AppSheet acepta tablas de archivos distintos; no hace falta unificarlas.)
4. Configurar las relaciones en **Data → Columns**:
   - En CONTACTOS, ACTIVIDADES y PROPUESTAS: columna `ID_EMPRESA` → tipo
     **Ref** → tabla `bd_empresas`.
   - En ACTIVIDADES: `ID_CONTACTO` → **Ref** → `bd_contactos`.
   - Con eso, la ficha de cada empresa muestra automáticamente sus contactos,
     actividades y propuestas (vistas "Related").
5. Tipos de columna útiles: `FECHA*` → Date · `CONTACTADO/RESPUESTA/LICITA` →
   Yes/No · `ESTADO_CONTACTO` y `ESTADO` (actividades/propuestas) → Enum con
   los valores del diccionario · `LINKEDIN_FUENTE` → Url.
6. Vistas sugeridas (**UX → Views**):
   - **Cola** — tabla de EMPRESAS ordenada por `PRIORIDAD`/score, filtro
     `ALERTA` vacía.
   - **Ficha empresa** — detail view con los Related Contactos/Actividades.
   - **Nueva actividad** — form sobre ACTIVIDADES (lo que carga el vendedor
     después de cada llamada/visita).
   - **Vencimientos** — ACTIVIDADES con `ESTADO=abierta` y
     `FECHA_PROXIMO <= TODAY()`.
7. **Share** → invitar a los vendedores con su mail de Google.

## Opción B — Glide

[glideapps.com](https://www.glideapps.com) es más lindo visualmente pero el
plan gratis rinde mejor con **una sola planilla**: en ese caso, abrir
BD 1 — EMPRESAS y, desde cada una de las otras tres planillas, clic derecho en
la pestaña → **Copiar en → Hoja de cálculo existente → BD 1**. Quedan las 4
tablas como pestañas de un solo archivo y Glide las toma todas juntas.

(Esa consolidación en un solo archivo también sirve para AppSheet si se
prefiere tener todo junto; las relaciones se configuran igual.)

## Score de la cola dentro de la app

El campo score que calcula `agentes/priorizador.py` se puede reproducir en
AppSheet como columna virtual, pero lo más simple es correr el priorizador
cuando haga falta y pegar la cola generada
(`agentes/salidas/cola_trabajo_*.csv`) en una pestaña "COLA" de la planilla:
la app la muestra tal cual y el criterio queda en un solo lugar (el script).

## Regla de oro

La app **escribe** en ACTIVIDADES y PROPUESTAS y **lee** EMPRESAS y CONTACTOS.
Ediciones de los maestros (corregir un cargo, marcar `VERIFICADO=SI`) mejor
hacerlas desde la planilla, con criterio, no desde el formulario de venta.
