# Contrato de respuesta de la IA

Este es el contrato lógico v0.1 entre el narrador y la aplicación local. Es una especificación; todavía no se ha conectado ni probado con un proveedor.

## Forma general

Cada turno debe devolver un objeto con estos apartados:

- `narracion`: texto que verá el usuario.
- `eventos`: acciones/reacciones observables narradas en ese turno.
- `cambios_propuestos`: operaciones sugeridas para el estado.
- `tiempo`: duración narrativa propuesta y motivo.
- `movimientos`: cambios de ubicación propuestos para entidades distintas del protagonista.
- `operaciones_inventario`: añadir, retirar, usar, transferir o cambiar el estado de un objeto, siempre ligado a un evento.
- `usos_de_poder`: intento, objetivo, resultado y coste de cada poder utilizado.
- `pendientes`: ambigüedades, propuestas de alto impacto o información que falta.

Los campos deben existir en cada respuesta aunque las listas estén vacías. No se deben incluir estadísticas inventadas para completar campos.

## Ejemplo ilustrativo

El siguiente ejemplo muestra la separación de diálogo y cambios. Es una posibilidad de respuesta, no una reacción canon obligatoria de Maelis.

```json
{
  "narracion": "Maelis te mira con extrañeza. «¿En serio? Apenas te conozco. ¿Por qué hablas así?». Se aparta un poco, incómoda. Ivar suelta una risa breve; Brina lo reprende con una mirada.",
  "eventos": [
    {
      "id": "ev-0001",
      "tipo": "dialogo_usuario",
      "emisor": "protagonista",
      "destinatario": "maelis-orven",
      "contenido": "Hola, linda"
    },
    {
      "id": "ev-0002",
      "tipo": "reaccion_pnj",
      "entidad": "maelis-orven",
      "contenido": "Responde con incomodidad ante una familiaridad inesperada",
      "testigos": ["ivar-dalen", "brina-solcor"]
    },
    {
      "id": "ev-0003",
      "tipo": "reaccion_pnj",
      "entidad": "ivar-dalen",
      "contenido": "Se ríe brevemente ante el intercambio",
      "testigos": ["maelis-orven", "brina-solcor"]
    }
  ],
  "cambios_propuestos": [
    {
      "id": "chg-0001",
      "entidad": "maelis-orven",
      "campo": "confianza",
      "operacion": "delta",
      "valor": -1,
      "motivo": "La familiaridad no solicitada le resulta incómoda en este contexto",
      "evento_fuente": "ev-0002",
      "confianza_modelo": 0.72,
      "requiere_aprobacion": false
    },
    {
      "id": "chg-0002",
      "entidad": "maelis-orven",
      "campo": "impresion_temporal",
      "operacion": "establecer",
      "valor": "El protagonista parece demasiado familiar o atrevido",
      "motivo": "Reacción inmediata al saludo",
      "evento_fuente": "ev-0002",
      "confianza_modelo": 0.82,
      "requiere_aprobacion": false
    }
  ],
  "tiempo": {
    "minutos_propuestos": 1,
    "motivo": "Intercambio breve"
  },
  "movimientos": [],
  "operaciones_inventario": [],
  "usos_de_poder": [],
  "pendientes": []
}
```

## Reglas de validación del contrato

1. Los IDs deben existir en la base local o estar incluidos en una propuesta explícita de creación permitida.
2. Cada cambio debe referenciar un evento del mismo turno.
3. `confianza_modelo` mide incertidumbre de la IA; no es una estadística de la relación ni sustituye la evidencia.
4. `requiere_aprobacion` puede solicitar revisión, pero no evita las comprobaciones locales.
5. Los valores numéricos deben respetar los límites del campo.
6. Un `delta` no se ejecuta dos veces si se reintenta el mismo turno; cada operación lleva un ID idempotente.
7. Las operaciones de inventario deben incluir objeto, cantidad, tipo de operación y evento causante.
8. Los usos de Eco deben vincularse a objetivo, intento, resultado y coste. El programa aplica el contador; la IA no puede recargarlo.
9. Si la narración dice que una acción ocurrió, pero el cambio correspondiente es inválido, se registra una discrepancia y no se altera silenciosamente el estado.
10. El programa conserva la respuesta original de la IA, las propuestas, la decisión del validador y el resultado final.

## Tipos de operación previstos

- `establecer`: asignar un valor permitido.
- `delta`: proponer un incremento/decremento numérico.
- `añadir`: crear o añadir una cantidad de objeto.
- `retirar`: consumir o eliminar una cantidad por una causa válida.
- `transferir`: cambiar de portador o ubicación.
- `registrar_evento`: añadir un hecho, observación, rumor o hipótesis con tipo y fuente.

No se implementará aceptación automática de cualquier campo nuevo. El modelo de datos fija qué campos existen; los demás se rechazan o se dejan como propuestas pendientes.


## Compatibilidad con OpenAI y Gemini

La API de OpenAI ofrece Structured Outputs en modelos/endpoints compatibles; Gemini ofrece salida estructurada basada en JSON Schema. El adaptador de cada proveedor transforma la llamada y normaliza la respuesta al contrato común. Referencias oficiales:

- OpenAI: https://developers.openai.com/api/docs/guides/structured-outputs
- Gemini: https://ai.google.dev/gemini-api/docs/structured-output

Usar salida estructurada cuando esté disponible; no depender únicamente de que el prompt diga «devuelve JSON». El contrato se mantendrá en un subconjunto común de los dos proveedores y se probará con los modelos elegidos. No todos los elementos de JSON Schema son compatibles en todas las APIs.

**Validación estructural y semántica son etapas distintas.** Primero se comprueba el formato; luego se comprueba que la operación esté permitida por el estado local, las reglas del mundo y el acontecimiento fuente. Un campo válido puede proponer un valor falso, duplicado o incoherente.

### Identificadores e idempotencia

Los IDs legibles del ejemplo (`ev-0001`, `chg-0001`) son referencias locales al cuerpo de una única respuesta, no IDs globales de base de datos. Al recibir el resultado, la aplicación asigna `turn_id`, IDs persistentes de eventos y operaciones, y una clave de idempotencia. Un reintento del mismo turno no puede descontar otra unidad de Eco ni aplicar por segunda vez un delta de relación. No aceptar IDs de entidad arbitrarios propuestos por el modelo como si fueran autoridades.

### Resultado cuando una propuesta no pasa la validación

- Narración separable y no contradictoria: se puede mostrar, con la discrepancia anotada.
- Operación inválida: no se aplica a la base de datos.
- Narración que afirma una compra, muerte, movimiento o uso de poder mientras los datos correspondientes no pasan la validación: marcar discrepancia y solicitar reparación o revisión; no fingir que el estado fue actualizado.
- Respuesta no analizable: mantener el estado anterior y reintentar una sola vez con una instrucción de reparación, si el límite de gasto y seguridad lo permite.
