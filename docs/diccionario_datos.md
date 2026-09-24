# Diccionario de datos

## bd_empresas.csv (376 filas)

| Columna | Descripción |
|---|---|
| ID_EMPRESA | Clave primaria `EMP-0001…EMP-0376`. Orden: hoja 1 original (Z→A) y luego cuentas agregadas (pestaña COMEDORES / detectadas en relevamiento). |
| EMPRESA | Nombre canónico de la cuenta. |
| ORIGEN | `Hoja 1`, `COMEDORES`, `COMEDORES (sin relevar)`, `Sugerida`, `Derivada Ternium`, `Detectada en relevamiento`. |
| LOCALIDAD | Localidad declarada en la hoja original o verificada en relevamiento. |
| PRIORIDAD | Prioridad 1/2/3 asignada por el equipo comercial en la hoja original. |
| ESTADO_PIPELINE | Campo ESTADO de la hoja original (texto libre: "EN CONVERSACION", "ENVIAR PRESUPUESTO", "arranca oct", …). |
| CONTACTADO / RESPUESTA / LICITA | SI/NO de la hoja original. |
| TIPO_SERVICIO | VIANDA / COMEDOR (hoja original). |
| PROVEEDOR_ACTUAL | Competidor detectado (hoja original). |
| FECHA_ULT_CONTACTO / FECHA_VOLVER_CONTACTAR | Fechas del seguimiento manual previo. |
| MAIL_GENERAL / TELEFONO_CEL | Canal institucional o celular de la hoja original. |
| CONTACTO_HISTORICO | Persona anotada a mano en la hoja original (columna CONTACTO PERSONAL + nombre). |
| TAMANO_ESTIMADO | Dotación estimada hallada en el relevamiento (solo donde hay fuente). |
| ALERTA | `CERRADA`, `DUPLICADO de …`, `VERIFICAR: …`, `NO IDENTIFICADA — …`. Filtrar antes de invertir esfuerzo comercial. |
| COMENTARIOS_PROPIOS | Comentarios del equipo en la hoja original. |
| OBSERVACIONES_RELEVAMIENTO | Notas del relevamiento (canales alternativos, teléfonos, direcciones verificadas, contexto). |
| N_CONTACTOS | Cantidad de filas en bd_contactos para esta cuenta (0 = solo canal institucional). |

## bd_contactos.csv (314 filas)

| Columna | Descripción |
|---|---|
| ID_CONTACTO | Clave primaria `CON-0001…`. |
| ID_EMPRESA / EMPRESA | Clave foránea y nombre desnormalizado para lectura rápida. |
| NOMBRE / CARGO | Como aparecen en la fuente (cargo textual). |
| AREA | Normalizada: `Compras`, `RRHH`, `Planta/Operaciones`, `Administración/Finanzas`, `Dirección/Dueño`, `Otro`. |
| SENIORITY | Solo cargada en la pasada focalizada (gerente/jefe/analista/…). |
| LINKEDIN_FUENTE | URL de LinkedIn, o la fuente entre paréntesis (RocketReach/ZoomInfo/web oficial/Boletín Oficial) cuando no hay perfil indexado. |
| EMAIL | Solo cuando la identidad del mail está confirmada (22 casos). |
| CONFIANZA | Alta / Media / Baja (y combinaciones). Baja = verificar antes de usar. |
| VERIFICADO | `NO` por defecto. Pasar a `SI` cuando alguien del equipo confirme el cargo en LinkedIn/teléfono. |
| ESTADO_CONTACTO | `nuevo` → `contactado` → `respondió` / `sin respuesta` / `descartado` (lo administran los agentes). |
| FECHA_RELEVAMIENTO / FUENTE | Trazabilidad del dato (21-09 barrido general / 22-09 pasada Compras-RRHH). |
| NOTAS | Contexto, correcciones (p. ej. "posible EX", "verificar sede"). |

## bd_actividades.csv

`ID_ACTIVIDAD, FECHA, ID_EMPRESA, ID_CONTACTO, RESPONSABLE_AGENTE, TIPO (email/llamada/whatsapp/linkedin/visita/propuesta), DIRECCION (saliente/entrante), RESUMEN, RESULTADO, PROXIMO_PASO, FECHA_PROXIMO, ESTADO (abierta/cerrada)`

Una fila por interacción. Es la fuente de verdad del pipeline vivo; la fila de ejemplo `ACT-0001` puede borrarse.

## bd_propuestas.csv

`ID_PROPUESTA, ID_EMPRESA, FECHA, TIPO_SERVICIO, CANT_PERSONAS_ESTIMADA, TURNOS, PRECIO_OFERTADO, ESTADO (borrador/enviada/negociación/ganada/perdida), LINK_DOCUMENTO, NOTAS`

## Datos conocidos a corregir en la hoja original

1. Columna DIRECCIÓN desfasada respecto de CLIENTE (excluida del maestro).
2. Duplicados: `Gerdau — Planta Pérez` = `Sipar`; `EPRECCO PIÑEIRO` = `EPRECO`; `Grupo Brayco` = `SEMAC`; `Calidad Asegurada en Aguas` = grupo S&D/SADE; `ACEIRA???` = Acindar.
3. `Adient` cerró su planta (06/2026): no prospectar.
4. Identidad a confirmar: SMP, IRT, Mercator, Selecta, ABC Comex, rava, TENSAR, DANES, FIUME, EXPRESS CORP, CAI, ACA Venado. (PECAM y DYSCON resueltos: son clientes actuales.)
5. `Victoria Rios Ordoñez` (Unilever) no es RRHH (corregido en bd_contactos).
6. `Matías Fernández` (compras Electrolux) podría ser de Curitiba (BR): verificar.

## Reset de pipeline (24-09-2026)

Antes de lanzar la campaña se pusieron en 0 los campos de seguimiento heredados
de la hoja original (`ESTADO_PIPELINE`, `CONTACTADO`, `RESPUESTA`,
`FECHA_ULT_CONTACTO`, `FECHA_VOLVER_CONTACTAR`), preservando la marca
`CLIENTE ACTUAL`. El estado previo quedó archivado en
`data/fuentes/pipeline_previo_20260924.csv`. El seguimiento vivo desde esa
fecha es la base compartida de la app (actividades / cuentas_meta).
