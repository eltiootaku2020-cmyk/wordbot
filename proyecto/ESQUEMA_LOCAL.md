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

### `ability_uses`
- `id`, `session_id`, `ability_key`, `user_entity_id`, `target_entity_id`, `attempt_number`, `result`, `cost_applied`, `event_id`, `created_at`.
- El programa valida los límites de usos por objetivo y evita duplicar un gasto al reintentar el mismo turno.

### `snapshots`
- `id`, `session_id`, `event_sequence`, `state_json`, `created_at`, `label`.
- Copia útil para restauración; no sustituye al registro de eventos.

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
