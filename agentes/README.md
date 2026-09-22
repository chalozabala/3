# Agentes de la fuerza de venta

Cuatro agentes que operan sobre `data/`. Corren con Python 3 sin instalar nada
(el modo `--ia` es opcional y requiere `pip install anthropic` + una API key de
Anthropic en `ANTHROPIC_API_KEY`).

| Agente | Qué hace | Escribe en |
|---|---|---|
| `priorizador.py` | Rankea las cuentas y arma la cola de trabajo | `salidas/cola_trabajo_*.csv` |
| `propuesta.py` | Genera el borrador de propuesta de una cuenta | `salidas/propuestas/` (+ fila en `bd_propuestas` con `--registrar`) |
| `contacto.py` | Redacta mail + mensaje de LinkedIn por contacto | `salidas/borradores/` (+ `bd_actividades` con `--registrar-envio`) |
| `seguimiento.py` | Lista vencimientos (actividades y "volver a contactar") | solo informa |

## Ciclo semanal sugerido

```bash
# Lunes: armar la cola de la semana
python3 agentes/priorizador.py --top 40

# Ver el detalle de una cuenta antes de trabajarla
python3 agentes/priorizador.py --detalle EMP-0297

# Generar la propuesta cuando la cuenta lo pide
python3 agentes/propuesta.py --empresa EMP-0297 --tipo comedor --registrar

# Redactar el primer contacto del mejor contacto de la cuenta
python3 agentes/contacto.py --empresa EMP-0297

# ...la persona revisa el borrador, completa los [corchetes] y ENVÍA A MANO...

# Después de enviar, dejar registro (esto alimenta al de seguimiento)
python3 agentes/contacto.py --contacto CON-0210 --registrar-envio email

# Todos los días: qué vence hoy
python3 agentes/seguimiento.py
```

## Reglas de operación (no negociables)

1. **Nada se envía solo.** Los agentes producen borradores; una persona revisa,
   completa los `[COMPLETAR]`/`[GANCHO]` y envía desde su propio mail/LinkedIn.
2. **LinkedIn siempre manual** desde la cuenta propia. Automatizar acciones
   dentro de LinkedIn viola sus términos y arriesga la cuenta.
3. **Verificar antes de contactar.** `CONFIANZA` y `VERIFICADO=NO` en
   `bd_contactos` avisan que el cargo salió de fuentes públicas y puede estar
   desactualizado. Verificado el cargo, marcar `VERIFICADO=SI`.
4. **Todo lo que pasa se registra** en `bd_actividades` (via
   `--registrar-envio` o a mano): es la fuente de verdad del pipeline y lo que
   lee el agente de seguimiento.
5. Los maestros (`bd_empresas`, `bd_contactos`) solo se editan para corregir,
   verificar o enriquecer datos, nunca desde la operación diaria.

## El quinto agente (enriquecimiento)

Cerrar los huecos que marca la cola (`Derivar al agente de enriquecimiento`),
las cuentas `NO IDENTIFICADA` y los contactos sin URL es trabajo de
investigación, no de script: se hace con sesiones de Claude (como los
relevamientos del 21 y 22-09) pidiéndole que actualice `bd_empresas` /
`bd_contactos` con fuentes citadas.

## Sincronización con Google Drive

Hoy la copia operativa vive en este repo y las 4 planillas de Drive son el
espejo para consultar/compartir. Después de una tanda de cambios, re-exportar
los CSV a Drive (o pedirle a Claude que lo haga). Si el aplicativo se monta
sobre AppSheet/Glide (ver `docs/aplicativo_appsheet.md`), Drive pasa a ser la
copia operativa y este repo queda como respaldo versionado.
