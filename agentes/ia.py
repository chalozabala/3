# -*- coding: utf-8 -*-
"""Pulido opcional de borradores con la API de Claude (flag --ia de los agentes).

Requiere `pip install anthropic` y ANTHROPIC_API_KEY en el entorno (o un perfil
de `ant auth login`). Sin credenciales, los agentes funcionan igual en modo
plantilla: la IA solo mejora la redacción, nunca inventa datos ni envía nada.
"""

MODELO = "claude-opus-5"

SYSTEM = (
    "Sos el redactor comercial de una empresa argentina de servicio de comedor y "
    "viandas para plantas industriales del cordón Gran Rosario–San Lorenzo–San Nicolás. "
    "Recibís un borrador generado por plantilla más datos de contexto de la cuenta. "
    "Devolvé SOLO el borrador reescrito, en español rioplatense profesional (trato de "
    "usted), más natural y específico, manteniendo la misma estructura y largo similar. "
    "Reglas estrictas: no inventes datos, precios, clientes ni certificaciones; "
    "conservá intactos todos los marcadores [COMPLETAR: ...], [TU EMPRESA], [TU NOMBRE], "
    "[TELÉFONO], [MAIL], [WEB O CARPETA DE PRESENTACIÓN] y los bloques de advertencia "
    "que empiezan con '>'; si un dato de contexto es dudoso, dejalo como sugerencia "
    "entre corchetes en lugar de afirmarlo."
)


def pulir(borrador, contexto):
    import anthropic

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=MODELO,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Contexto de la cuenta (datos relevados, pueden estar incompletos):\n"
                    f"{contexto}\n\n---\n\nBorrador a reescribir:\n\n{borrador}"
                ),
            }],
        )
    except anthropic.AuthenticationError:
        print("  [ia] Sin credenciales válidas (ANTHROPIC_API_KEY). Queda el borrador de plantilla.")
        return borrador
    except anthropic.RateLimitError:
        print("  [ia] Límite de uso de la API alcanzado. Queda el borrador de plantilla.")
        return borrador
    except anthropic.APIStatusError as e:
        print(f"  [ia] Error de la API ({e.status_code}). Queda el borrador de plantilla.")
        return borrador
    except anthropic.APIConnectionError:
        print("  [ia] Sin conexión con la API. Queda el borrador de plantilla.")
        return borrador

    if response.stop_reason == "refusal":
        print("  [ia] La API declinó la solicitud. Queda el borrador de plantilla.")
        return borrador

    texto = "".join(b.text for b in response.content if b.type == "text").strip()
    return texto or borrador
