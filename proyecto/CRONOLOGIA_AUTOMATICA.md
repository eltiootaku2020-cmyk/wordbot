# Acontecimientos programados del mundo

**Estado de esta rama:** consolidación de las PR #21 y #23. La definición del acontecimiento es global al mundo; su ejecución es independiente por partida. La CI de esta rama debe validar las pruebas de integración antes de considerar cerrada esta etapa.

## Modelo único

La tabla `world_timeline_events` conserva:

- Una `stable_key` única dentro del mundo.
- Título y descripción.
- Tipo de activación: `fixed_time` o `condition`.
- Día y minuto cuando es una fecha fija.
- Condición estructurada en JSON, ámbito (`world` o `location`), ubicación y consecuencias estructuradas.
- Aprobación (`pending`, `approved`, `rejected`) y ciclo de vida (`active`, `cancelled`, `superseded`).

La tabla `session_timeline_runs` registra por partida cuándo se activó el suceso, en qué fecha debía ocurrir, qué turno o recuperación lo registró y el registro estructurado aplicado. La restricción única `(session_id, scheduled_event_id)` impide duplicaciones por reintentos.

## Activación y recuperación

- Los eventos nuevos nacen pendientes; no alteran el mundo hasta su aprobación explícita.
- Solo los eventos `fixed_time`, aprobados y activos pueden ejecutarse automáticamente.
- El avance normal del reloj usa el intervalo abierto/cerrado `(anterior, nuevo]`, en orden cronológico.
- Al crear una partida o aprobar/editar una definición aprobada, la recuperación busca sucesos cuya fecha ya venció y que aún no estén registrados en esa partida.
- Los eventos `condition` se pueden almacenar para diseño futuro, pero **no se evalúan ni ejecutan** en esta etapa.
- `condition` y `consequences` son objetos JSON; nunca se interpretan como código ni como instrucciones directas para la IA.
- El historial de ejecución de una partida no se comparte con otra partida del mismo mundo.

## API administrativa

- `POST /api/worlds/{world_id}/timeline`: crea una definición pendiente.
- `GET /api/worlds/{world_id}/timeline`: lista las definiciones y cuántas partidas ya registraron cada una.
- `PATCH /api/worlds/{world_id}/timeline/{event_id}`: edita una definición mientras ninguna partida la haya ejecutado.
- `POST /api/worlds/{world_id}/timeline/{event_id}/review`: aprueba o rechaza una definición. Aprobar un suceso vencido activa recuperación inmediata en las partidas existentes.
- `DELETE /api/worlds/{world_id}/timeline/{event_id}`: marca como cancelado un evento no ejecutado; no borra físicamente la definición.

Después de que una sola partida registre el acontecimiento, la definición queda protegida contra edición, rechazo o cancelación retroactiva. Para una versión distinta debe crearse otra clave estable.

Para un evento fijo, el objeto enviado al crear incluye `activation_type="fixed_time"`, `scheduled_day` y `scheduled_minute`. Para una condición, usa `activation_type="condition"`, omite día/minuto y conserva la condición como datos estructurados. Un evento de ámbito `location` necesita una ubicación.

## Conocimiento de personajes

Los hechos registrados en la cronología se incluyen en un bloque separado del contexto. Se informa que el hecho pertenece al mundo y que no implica que el protagonista o los PNJ lo conozcan. La IA no puede convertir un evento lejano en conocimiento de un personaje sin una fuente narrativa.

## Deshacer y copias

Los registros de ejecución forman parte de la instantánea del turno. Deshacer un turno restaura el reloj y el registro de activaciones de esa partida, de modo que un reintento no queda bloqueado por un evento que ya no pertenece al estado restaurado.

Las copias de partida incluyen `session_timeline_runs`. Las copias antiguas que no contienen esa tabla se siguen aceptando tratándola como vacía. Las definiciones globales no se copian ni restauran desde una copia individual de partida.

## Fuera del alcance

No se ejecutan condiciones, no hay motor de consecuencias autónomas, no se propagan automáticamente rumores/conocimientos, no existe un mapa geográfico ni cálculo de rutas. La UI guiada de la PR #23 prepara acciones y prompts para que el usuario los envíe; no desplaza al protagonista ni envía mensajes automáticamente.
