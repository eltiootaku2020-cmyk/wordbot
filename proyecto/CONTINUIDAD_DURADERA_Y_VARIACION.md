# Continuidad duradera y variedad narrativa

**Estado de esta entrega:** implementación propuesta en la rama `feat/continuity-memory-variety`; pendiente de CI y revisión. No declarar terminada hasta que pasen las pruebas.

## Problema que aborda

El gestor ya conserva en SQLite el reloj de la partida, la ubicación, la presencia de personajes, el inventario, los recursos, las relaciones dirigidas, los usos de habilidades, los eventos y las propuestas pendientes. El riesgo no era que todo eso se borrara en cada turno, sino que el constructor de contexto solo enviaba una ventana pequeña de eventos recientes y dos eventos antiguos por coincidencia léxica. Una promesa, herida, pista o conocimiento importante podía seguir guardado en SQLite y, aun así, no llegar al narrador.

También se enviaba la relación con el destinatario, pero no el conjunto de relaciones entre los personajes que comparten la escena.

## Cambios de esta entrega

### 1. Marcas de continuidad duradera

Los eventos ahora admiten:

- `continuity`: indica si el acontecimiento merece recuperarse como memoria duradera.
- `importance`: prioridad de 1 a 5.
- Categorías adicionales: `promise`, `quest`, `injury`, `clue`, `secret`, `deadline`, `threat`, `timeline_anchor`, `knowledge` y `tracked_fact`.

Las categorías duraderas se marcan automáticamente como continuidad. El narrador debe usar importancia 4–5 para datos importantes y 1 para sucesos cotidianos. Cada marca sigue necesitando un evento fuente válido y respeta los testigos y la audiencia de ese evento.

El constructor de contexto recupera hasta 12 marcas duraderas por separado de la ventana de eventos recientes. La selección se realiza después de aplicar los filtros de audiencia/testigos; por tanto, una conversación privada no se convierte en conocimiento de otro personaje. Las marcas también aparecen en el estado de la partida para inspección.

Una resolución no borra el acontecimiento original: debe narrarse como otro evento que identifique el hecho que resuelve. El historial permanece auditable.

### 2. Relaciones de escena

Además de `relationship_to_recipient`, el contexto incluye `relationships_in_scene`: relaciones dirigidas entre los personajes que participan en la escena. Esto permite al narrador recordar que dos PNJ tienen rivalidad, respeto, deuda, miedo o cooperación aunque el protagonista no sea uno de los extremos de ese vínculo.

En escenas privadas solo se incluyen relaciones entre el protagonista y el destinatario. No se inyectan vínculos de terceros en un intercambio privado.

### 3. Variación narrativa controlada

Cada turno recibe una sugerencia de estilo entre ocho posibilidades: detalle ambiental, iniciativa moderada de un PNJ, subtexto, obstáculo práctico, pausa, actividad independiente, observación sensorial o humor ligero.

La sugerencia se calcula de forma determinista a partir de la partida y el número de turno. El mismo prompt manual y su envío posterior reciben la misma sugerencia; los reintentos no cambian las instrucciones. Se evitan las tres sugerencias utilizadas más recientemente.

La variación afecta al modo de narrar, no a los resultados del mundo. No autoriza a inventar encuentros, objetos, peligros, relaciones, éxitos o fracasos. El narrador recibe además una instrucción explícita para evitar repetir frases, gestos, aperturas, bromas y estructuras de los últimos mensajes.

## Datos que el motor ya conserva

| Dato | Fuente persistente |
|---|---|
| Día, hora y ubicación | `sessions` |
| Personajes y fichas | `entities` |
| Ubicación/presencia de cada PNJ | `session_presence` |
| Objetos, cantidad, condición, portador y lugar | `inventory_items` |
| Recursos y saldos | `resources` |
| Relaciones dirigidas y por eje | `relationships` |
| Usos limitados por objetivo | `ability_uses` |
| Hechos, testigos y conocimiento de escena | `events` |
| Promesas, pistas, heridas, misiones y amenazas importantes | `events.continuity` + `events.importance` |
| Cambios aceptados, pendientes o rechazados | `state_changes` |

## Límites que siguen pendientes

1. **Cronología automática:** `timeline_anchor` permite marcar un acontecimiento fijo y conservarlo en contexto, pero todavía no existe un programador local que dispare el acontecimiento exactamente al cruzar el día/hora fijados. No afirmar que esta parte está implementada.
2. **Estado estructurado de heridas:** por ahora una herida relevante se conserva como evento duradero; todavía no hay un subsistema de salud con gravedad, tratamiento, infección y recuperación.
3. **Ciclo de vida de misiones/promesas:** se conserva el alta y la resolución como eventos históricos, pero todavía no existe una tabla de tareas activas con estados pendiente/cumplida/incumplida/cancelada y plazos verificables.
4. **Conocimiento de PNJ:** los testigos limitan qué eventos se recuperan; aún falta un modelo epistemológico más fino para distinguir quién lo vio, quién se lo contó y quién lo dedujo.
5. **Detección de repetición semántica:** la prevención actual se basa en contexto y sugerencias de estilo; no hay todavía un detector local de similitud que rechace narraciones casi duplicadas.
6. **Aleatoriedad del resultado:** no se aleatorizan las reglas ni los resultados. El proveedor externo conserva su propia configuración de generación; el modo simulado continúa siendo determinista.

## Criterios de aceptación

- Una promesa o pista importante de hace más de seis eventos sigue apareciendo en el contexto si su audiencia es válida.
- Una marca conocida solo por el protagonista no aparece en el contexto privado de otro PNJ.
- Las relaciones entre PNJ presentes aparecen en escena; los vínculos de terceros no se filtran a una escena privada.
- La sugerencia narrativa se mantiene idéntica entre preparación y envío del mismo turno.
- La sugerencia no repite ninguna de las tres últimas.
- Una sugerencia de estilo nunca crea por sí misma una operación de inventario, un cambio de relación ni un evento.
- El reloj y la ubicación siguen viniendo del estado persistido, no de una cabecera fija.
- Las pruebas existentes de idempotencia, privacidad, undo, recuperación y restauración continúan pasando.

