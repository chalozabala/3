# Base de datos comercial — Servicio de comedor/viandas Gran Rosario

Base de datos de prospección para armar la fuerza de venta y los agentes de IA
(propuesta, contacto, seguimiento) del servicio de comedor y viandas en el cordón
industrial Gran Rosario – San Lorenzo – Puerto Gral. San Martín – Timbúes – San Nicolás.

## Estructura

```
data/
  bd_empresas.csv      376 cuentas (1 fila por empresa)  — clave: ID_EMPRESA
  bd_contactos.csv     314 personas (1 fila por contacto) — clave: ID_CONTACTO → ID_EMPRESA
  bd_actividades.csv   bitácora de interacciones (vacía; la llenan vendedores/agentes)
  bd_propuestas.csv    registro de propuestas por cuenta (vacío)
  fuentes/             datos crudos: hoja original + relevamientos 21/22-09-2026
docs/
  diccionario_datos.md diccionario de columnas y reglas de uso
```

## Modelo relacional

`EMPRESAS 1—N CONTACTOS` · `EMPRESAS 1—N ACTIVIDADES` · `CONTACTOS 1—N ACTIVIDADES` · `EMPRESAS 1—N PROPUESTAS`

Toda escritura de los agentes va a **ACTIVIDADES** y **PROPUESTAS**; EMPRESAS y
CONTACTOS solo se actualizan al verificar o enriquecer datos (campo `VERIFICADO`,
`ESTADO_CONTACTO`, `ESTADO_PIPELINE`).

## Flujo previsto de agentes

1. **Agente priorizador**: rankea cuentas por tamaño estimado, área cubierta
   (Compras/RRHH con nombre) y estado del pipeline; arma la cola de trabajo diaria.
2. **Agente de propuesta**: con los datos de EMPRESAS (tipo de servicio, turnos,
   dotación) genera el borrador de propuesta y lo registra en PROPUESTAS.
3. **Agente de contacto (drafting)**: redacta el mail/mensaje personalizado por
   contacto (cargo + área + gancho de la cuenta). **El envío lo aprueba una persona**;
   el resultado se registra en ACTIVIDADES.
4. **Agente de seguimiento**: lee ACTIVIDADES, detecta vencimientos de
   `FECHA_PROXIMO` y regenera la cola.
5. **Agente de enriquecimiento**: cierra los huecos marcados (contactos sin URL,
   empresas `VERIFICAR`/`NO IDENTIFICADA`).

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
