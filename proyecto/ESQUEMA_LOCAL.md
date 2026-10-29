# Esquema local de datos — propuesta v0.1

SQLite es la fuente de verdad local. El esquema se mantendrá normalizado lo suficiente para consultar y validar el estado sin analizar de nuevo toda la conversación.

## Entidades principales

### `worlds`
- `id`, `name`, `description`, `canon_version`, `created_at`.
- Cada mundo tiene su propio espacio de nombres; no se cruzan IDs de mundos distintos.

### `sessions`
- `id`, `world_id`, `name`, `status`, `day`, `time_block`, `minutes_of_day`, `current_location_id`, `created_at`, `updated_at`.
- Una sesión representa una partida concreta, no el Lorebook entero.

### `characters`
- `id`, `world_id`, `name`, `aliases_json`, `sheet_json`, `canonical_status`, `created_at`.
- La ficha incluye personalidad, objetivos conocidos, habilidades confirmadas y límites. Las opiniones temporales se guardan por separado.

### `locations`
- `id`, `world_id`, `name`, `parent_location_id`, `description`, `access_rules_json`, `created_at`.

### `lore_entries`
- `id`, `world_id`, `title`, `keywords_json`, `content`, `entry_type`, `priority`, `enabled`, `source`, `canon_status`.
- Tipos: regla, personaje, lugar, poder, objeto, cronología, facción, referencia o gancho opcional.

### `messages`
- `id`, `session_id`, `turn_id`, `speaker`, `recipient_id`, `content`, `created_at`, `provider`, `model`, `generation_status`.
- Se conserva el texto íntegro del usuario y la narración final mostrada. Los intentos fallidos pueden conservarse con estado de error para diagnóstico.

### `events`
- `id`, `session_id`, `turn_id`, `event_type`, `description`, `source_message_id`, `evidence_json`, `knowledge_scope_json`, `status`, `created_at`.
- Estados/eventos: confirmado, observado, rumor, hipótesis, rechazado o pendiente. Registra quién presenció o conoce cada hecho.

### `state_changes`
- `id`, `session_id`, `event_id`, `entity_type`, `entity_id`, `field`, `old_value_json`, `proposed_value_json`, `accepted_value_json`, `status`, `reason`, `created_at`, `applied_at`.
- Conserva cambios aceptados, rechazados o pendientes. Permite rastrear por qué cambió un valor y revertirlo con seguridad.

### `inventory_items`
- `id`, `session_id`, `item_key`, `display_name`, `quantity`, `condition`, `carrier_entity_id`, `location_id`, `properties_json`, `last_event_id`.
- No se da por adquirido un objeto porque aparezca en un catálogo de posibilidades. Cada cambio de cantidad requiere un evento.

### `relationships`
- `id`, `session_id`, `from_entity_id`, `to_entity_id`, `axis`, `value`, `last_change_event_id`, `reason`, `updated_at`.
- Relación dirigida y por ejes independientes. No usar una única puntuación para definir todas las relaciones.

### `resources` (implementado en el prototipo)
- `id`, `session_id`, `resource_key`, `display_name`, `quantity`, `unit`, `last_event_id`, `updated_at`.
- Registra saldos por partida (monedas, cargas u otros recursos contables), separado del inventario físico.
- Restricción de cantidad no negativa y clave única por partida. Los ingresos/gastos deben asociarse a un evento fuente válido.
- Una compra se modela como adquisición de un objeto con coste total y clave de moneda; saldo, objeto y cambios de estado se actualizan en la misma transacción o no cambia ninguno.

### `ability_uses`
- `id`, `session_id`, `ability_key`, `user_entity_id`, `target_entity_id`, `attempt_number`, `result`, `cost_applied`, `event_id`, `created_at`.
- El programa valida los límites de usos por objetivo y evita duplicar un gasto al reintentar el mismo turno.

### `snapshots`
- `id`, `session_id`, `turn_id`, `event_sequence`, `state_json`, `created_at`.
- Snapshot del estado mutable anterior a cada turno, asociado con `turn_id`, para revertir la última respuesta sin recalcular el historial.
- Índice único por `session_id + turn_id` evita snapshots duplicados al reintentar un turno fallido.
- Un snapshot no reemplaza el registro de eventos; la versión anulada se conserva como auditoría.

### `provider_settings`
- `id`, `provider_key`, `model_key`, `endpoint_profile`, `settings_json`.
- Las claves API no deben almacenarse en texto plano dentro de la base de datos o el repositorio; usar el almacén seguro disponible en el sistema o variables protegidas.

## Transacciones e integridad

- La actualización de una respuesta se aplica como una transacción: guardar evento, cambio de estado y nueva secuencia juntos.
- Cada propuesta tiene identificador idempotente para que un reintento no aplique dos veces la confianza −1 ni gaste dos veces Eco.
- Los campos de valor restringido (porcentajes, cantidad, contador de usos, duración) se validan antes de escribir.
- Un guardado incluye la secuencia del último evento confirmado; una restauración permite volver a ese estado.
- Exportación e importación deberán validar el mundo y la versión del esquema antes de cambiar datos.

## Persistencia y copias de seguridad

La base de datos permanece en el PC. El usuario puede crear copias fechadas y exportar mundos/Lorebooks en formatos abiertos. Restaurar un guardado no debe cambiar el canon ni importar accidentalmente datos de otro mundo.


## Procedencia y recuperación

Toda entrada derivada de la narración debe conservar al menos la referencia al mensaje/turno que la originó y su estado de validación. Distinguir:
- canon aprobado;
- hecho confirmado de la partida;
- observación de un personaje concreto;
- rumor;
- hipótesis;
- propuesta no aceptada.

Para el conocimiento de PNJ, guardar quién sabe el hecho y la fuente por la que lo conoció. Un evento observado por un PNJ no se convierte automáticamente en conocimiento compartido por todo el grupo.

Los IDs y claves de idempotencia se generan en la aplicación. La IA puede usar referencias locales (por ejemplo `event_ref: "e1"`) solo para relacionar objetos dentro de una respuesta.

## Operación SQLite y copias

- Aplicar un turno aceptado con `BEGIN` / `COMMIT`; ante error, `ROLLBACK`.
- Evaluar WAL para lecturas concurrentes y escritura ligera local. WAL admite lectores concurrentes con un escritor activo y requiere que los procesos estén en el mismo equipo; no colocar la base viva en un sistema de archivos de red.
- No crear una copia consistente de una base activa copiando a ciegas solo el archivo principal si WAL está habilitado. Preferir la SQLite Online Backup API o un mecanismo que respete el estado de la base.
- Restaurar primero en un archivo temporal, verificar el esquema y la integridad, y permitir que el usuario confirme antes de reemplazar una partida activa.

Referencias oficiales:
- Transacciones: https://www.sqlite.org/lang_transaction.html
- WAL: https://www.sqlite.org/wal.html
- Backup API: https://www.sqlite.org/backup.html

## Claves y superficie local

- No incluir claves de proveedor en el repositorio, en Lorebooks ni en exportaciones de mundos.
- Preferir el almacén seguro del sistema operativo; como alternativa de desarrollo, archivo local ignorado por Git y con permisos restringidos.
- El servidor escucha en loopback por defecto, sin abrir la aplicación a la red doméstica/Internet.
- Las llamadas al proveedor incluyen solo el contexto requerido; las fichas y todo el historial de la partida permanecen en la base local salvo los mensajes seleccionados para generación.
