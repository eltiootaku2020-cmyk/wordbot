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
