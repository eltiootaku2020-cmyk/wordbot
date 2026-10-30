# Contrato de respuesta de la IA

Este es el contrato lógico v0.1 entre el narrador y la aplicación local. El prototipo ya implementa una versión Pydantic del contrato para el narrador simulado y adaptadores iniciales OpenAI/Gemini; la CI prueba el contrato con proveedor simulado, no las APIs reales. El JSON del ejemplo es ilustrativo y usa nombres en español; la implementación Python usa nombres de campos definidos en `models.py`.

## Forma general

Cada turno debe devolver un objeto con estos apartados:

- `narracion`: texto que verá el usuario.
- `eventos`: acciones/reacciones observables narradas en ese turno.
- `cambios_propuestos`: operaciones sugeridas para el estado.
- `tiempo`: duración narrativa propuesta y motivo.
- `movimientos`: cambios de ubicación propuestos para entidades distintas del protagonista.
- `operaciones_inventario`: añadir, retirar, usar, transferir o cambiar el estado de un objeto, siempre ligado a un evento; una compra incluye `cost` (coste total) y `currency_key`.
- `operaciones_recursos`: ingresos/gastos de recursos como salarios o recompensas que no estén ya contabilizados dentro de la compra de un objeto. Cada operación requiere evento de tipo `resource`, clave, cantidad, nombre y causa.
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


## Extensión implementada: recursos y compras

En la implementación Python real, `NarratorResponse` dispone de `resource_ops`; `EventProposal.kind` incluye `resource`; y cada `InventoryOperation` de tipo `acquire` puede declarar `cost` y `currency_key`.

Reglas semánticas:
1. Compra: evento fuente `object`, adquisición explícita, coste total positivo, clave de moneda existente y saldo suficiente.
2. El validador descuenta la moneda y añade el objeto en la misma transacción. Si falta el coste, la moneda o el saldo, la propuesta queda pendiente y no modifica ninguno de los dos.
3. No se debe emitir un `resource_ops spend` para el mismo evento de compra porque duplicaría el cargo; el validador también protege ese caso.
4. Ingresos de monedas y otros gastos requieren un evento fuente `resource` y texto que indique explícitamente el ingreso/gasto. Las cantidades se validan en SQLite.
5. Isekai sin Destino comienza con 0 monedas, en coherencia con el canon inicial sin dinero.

El proveedor simulado y las pruebas automáticas verifican compra suficiente, insuficiente y recompensa. Falta probar estos casos con un proveedor API real.


## Procedencia de testimonios y rumores

El contrato de eventos admite ahora los campos opcionales:

- `source_entity_id`: entidad que transmite el relato.
- `about_event_id`: ID persistente del acontecimiento que el hablante dice conocer.

El tipo de evento puede ser `testimony` o `rumor`. En ambos casos:

1. El hablante debe existir en el mundo y figurar entre los testigos autorizados del evento de transmisión.
2. El acontecimiento citado debe existir en la misma partida y continuar registrado.
3. El hablante debe tener un registro activo de conocimiento sobre ese acontecimiento. No basta con que el modelo afirme que lo sabe.
4. La audiencia/los oyentes se limita a los testigos autorizados de la transmisión.
5. Si el registro de origen es `rumor`, la información recibida sigue siendo `rumor`, aunque el evento nuevo se haya etiquetado como `testimony`.
6. Un rumor o testimonio nunca transforma el evento original en un hecho nuevo ni confirma automáticamente la identidad de un responsable.

El contexto incluye `known_information` con `knower_entity_id`, `knowledge_kind`, `about_event_id`, `transmission_event_id`, fuente, contenido y una nota epistemológica. Para el narrador, `rumor` significa «no confirmado» y `testimony` significa «relato de una fuente, no prueba por sí solo». El contenido de un rumor no se presenta como descripción del acontecimiento original.

Los eventos ordinarios registrados generan automáticamente conocimiento directo para sus testigos. Los eventos `rumor` y `testimony` generan registros de transmisión únicamente para sus oyentes; el hablante conserva su registro de origen y no recibe un duplicado de sí mismo.

El registro se consulta solo para el protagonista y el destinatario activo, evitando que el conocimiento privado de un PNJ se filtre a otro por compartir ubicación. La tabla conserva auditoría, pero una entrada deja de estar activa si el evento de transmisión o el acontecimiento original fue anulado/rechazado.

**Fuera del alcance actual:** propagación automática entre ciudades y facciones, reputación pública, clasificación de evidencias y atribución forense. La IA no puede inventar estos resultados por prompt.


## Evidencia, atribución y reputación local

La respuesta puede incluir tres listas opcionales: `evidence`, `attributions` y `reputation_changes`.

### Evidencia
Cada pieza identifica `event_ref` (evento de descubrimiento del turno actual), `about_event_id` (acontecimiento investigado ya registrado), `discovered_by_entity_id`, `evidence_kind`, `effect` y descripción. Quien la aporta debe ser testigo autorizado del hallazgo y tener una observación directa o un testimonio recibido y persistido. El rumor no sirve como evidencia.

### Atribución
Los niveles son distintos y no intercambiables:
- `description`: descripción sin identificar una entidad.
- `suspected`: entidad sospechosa, con al menos un indicio de apoyo.
- `identified`: exige dos observadores independientes con conocimiento directo registrado.
- `confirmed`: siempre queda pendiente; la IA no puede declarar culpabilidad confirmada.

Una identificación no es un veredicto. Los indicios contradictorios pueden quedar registrados sin borrar silenciosamente evidencia previa.

### Reputación local
`reputation_changes` enlaza la entidad, el nivel de atribución, el evento de transmisión y el ámbito. Esta versión solo acepta `scope_type="location"` y exige que `scope_key` coincida con la ubicación actual. El evento de transmisión debe ser `testimony` o `rumor` y llegar al menos a un PNJ que no sea el protagonista, el hablante ni la entidad señalada. Un rumor solo puede difundir una sospecha. El cambio máximo es 1 punto para sospecha y 2 para identificación; los valores se mantienen entre −100 y 100.

Un crimen secreto sin oyentes externos no genera reputación local. La reputación no es global: el valor de una ciudad/ubicación no se copia a otra. Los ámbitos de gremio, facción y caravana quedan pendientes hasta implementar membresías verificables y su propagación.

## Percepciones individuales, evidencia y atribución

Un evento puede incluir `perceptions`, una lista de registros personales del testigo. Cada entrada lleva `observer_entity_id`, `modality`, `observed_details`, `identity_assessment` y, únicamente para `suspected` o `recognized`, `claimed_entity_id`. El observador debe figurar en los testigos y dentro de la audiencia autorizada del evento. Una descripción parcial no identifica por sí sola a una persona.

`known_perceptions` se filtra por el conocimiento activo del protagonista y del destinatario. No se entrega la percepción privada de otro PNJ solo porque esté presente en la misma escena. `recognized` significa que ese observador declara reconocer a la persona; no prueba que la persona cometiera el hecho.

`EvidenceProposal` conserva la relación entre evento investigado y evento de descubrimiento, la entidad descubridora, clase de evidencia, efecto (`supports`, `contradicts`, `neutral`), procedencia del conocimiento y descripción. Una pista no confirma una identidad ni culpabilidad por sí sola. Los rumores nunca pueden usarse como evidencia.

Los niveles de atribución son `description`, `suspected`, `identified` y `confirmed`. Una identificación requiere al menos dos observadores distintos con conocimiento directo y una percepción `recognized` de cada uno que nombre al mismo sujeto. Si falta ese reconocimiento explícito, la atribución queda pendiente. `confirmed` siempre exige revisión explícita y nunca puede aceptarse solo por la respuesta de la IA.

La reputación se conserva por ubicación, no como fama mundial. Solo cambia cuando una atribución `suspected` o `identified` válida se transmite mediante testimonio/rumor registrado a oyentes externos al protagonista y al hablante. Un rumor solo difunde sospecha y los cambios automáticos están limitados a 1 punto para sospecha y 2 para identificación.

Las tablas de conocimiento, percepciones, evidencia, atribuciones y reputación se incluyen en las copias/restauraciones. Las copias antiguas que no tienen alguna de estas tablas se aceptan como datos vacíos para esa función; el conocimiento individual faltante se reconstruye solo a partir de eventos registrados y testigos válidos, nunca inventando percepciones, pistas o atribuciones históricas.