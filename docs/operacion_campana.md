# Operación de la campaña de contacto inicial — Arsa Catering

Guía para retomar la operación en cualquier sesión de Claude.

## Piezas

- **App "Recorrida"** (artifact claude.ai): https://claude.ai/artifact/VWeg1EV7PzyeYi3Jq6VZTn
  Pestaña **Campaña**: cola de pendientes por canal (mail 228 / LinkedIn 90),
  mensaje armado por cuenta, botones Abrir/Copiar/✓ Enviado/Omitir.
  También existe como archivo local `aplicativo/Recorrida.html` (modo localStorage).
- **Página con los textos definitivos**: https://claude.ai/artifact/R2KRyWNeXEHn8Q2rDUZQB2
- **Base compartida del artifact** (leer/escribir con la herramienta ArtifactData):
  colecciones `actividades` (bitácora, campo `campana:true` para envíos de campaña),
  `cuentas_meta` (estado/f_volver/nota/omitidas por canal), `contactos_meta`
  (verificado), `config` (doc `perfil`: nombre, empresa, tel, web).
- **Maestros**: `data/bd_empresas.csv` y `bd_contactos.csv` → `aplicativo/build_datos.py`
  genera `datos.js` → republicar el artifact y regenerar `Recorrida.html`
  (`aplicativo/build_local.py`).

## El mensaje (validado 22-09-2026)

Un solo mail (ver `agentes/plantillas/mail_compras.md` / `mail_rrhh.md` /
`mail_general.md`): asunto "Alimentación del personal en {EMPRESA}", firma
"Arsa Catering — comedores y viandas industriales / Rosario · Arroyo Seco ·
La Plata (Bs. As.)". Clientes de referencia: Sidersa, Inbelt, Pecam, Dinale,
Policlínico Unión. WhatsApp fuera de esta primera instancia.

## Envío

- Remitente: **comercial@arsacatering.com** (Google Workspace).
  DNS al 22-09: SPF ✓ · falta DMARC (`_dmarc` TXT
  `v=DMARC1; p=none; rua=mailto:comercial@arsacatering.com`) · falta activar
  DKIM en admin.google.com.
- Ritmo: 15–25 mails/día (10/día la primera semana si la casilla estuvo
  inactiva), chips ✓ verificados primero.
- **Nada se envía sin revisión humana.** LinkedIn siempre manual desde la
  cuenta propia. Cada envío se registra con "✓ Enviado" (crea la actividad con
  seguimiento a 7 días) — o, si Claude prepara borradores en Gmail, registrar
  el envío en la base al confirmarse.

## Tareas típicas para Claude

- "Armá la tanda de hoy": tomar pendientes de mail (mismo criterio que la app:
  activas, no cerradas/ganadas, sin actividad de tipo email, no omitidas,
  dedupe por casilla, EX excluidos), generar borradores en la casilla conectada
  (conector Gmail = comercial@) y registrar en `actividades` al enviarse.
- "¿Cómo viene la campaña?": leer `actividades` y resumir enviados/respuestas/vencidos.
- "Actualizá la app": editar `data/`, correr `build_datos.py` + `build_local.py`,
  republicar el artifact (URL de arriba) y reenviar `Recorrida.html`.
