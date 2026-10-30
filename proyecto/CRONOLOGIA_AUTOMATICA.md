# Acontecimientos programados del mundo

**Estado:** primera capa implementada en `feat/generic-scheduled-world-events`. Pendiente de CI, revisión y pruebas manuales. No está integrada en `main`.

## Modelo común

Los acontecimientos se definen por mundo en `world_timeline_events`; su ejecución se registra por partida en `session_timeline_runs`. Esto permite reutilizar la cronología de un mismo mundo en varias partidas sin compartir sus historiales de ejecución.

Cada definición conserva una clave estable, título, descripción, tipo de activación, fecha/hora (si es fija), condición estructurada, ámbito/ubicación, consecuencias, aprobación y ciclo de vida.

## Regla de ejecución implementada

- Solo se disparan automáticamente acontecimientos de tipo `fixed_time`, aprobados y activos.
- La ventana temporal es abierta en el reloj anterior y cerrada en el nuevo: `(anterior, nuevo]`.
- Los eventos atravesados se procesan en orden cronológico, incluidos los de saltos que cubran varios días.
- La ejecución se registra en la misma transacción que avanza el reloj.
- La restricción única por partida y acontecimiento evita duplicados en reintentos.
- Una definición pendiente/rechazada, cancelada/sustituida o basada en condición no se dispara automáticamente.
- Las condiciones se almacenan como datos; no se evalúan como código ni se delegan a la IA.
- El registro de ejecución no concede conocimiento al protagonista. El mensaje aplicado avisa expresamente que el hecho puede haber ocurrido fuera de escena.

## Límites pendientes

1. Endpoints/operaciones para crear, editar, aprobar, cancelar y sustituir definiciones con validación de permisos.
2. Evaluador seguro de condiciones con operadores y campos permitidos, sin expresiones ejecutables.
3. Presentación diferenciada de hechos globales, locales y conocidos por personajes; todavía no se propagan conocimientos.
4. Política explícita de deshacer: una cronología mundial no debe duplicarse ni retroceder accidentalmente cuando se deshace un turno.
5. Pruebas de migración con una base SQLite antigua, copia/restauración, reinicio y campaña de varios días.
6. CI y pruebas manuales en Windows/Chromium.

## Criterios mínimos cubiertos por pruebas nuevas

- Un evento del Día 5 se registra al cruzar de Día 4 a Día 5.
- Un salto que atraviesa varios eventos los registra todos y en orden.
- Reintentar la misma operación no duplica el registro.
- Los eventos condicionales o pendientes de aprobación no se disparan.
- El registro está aislado por partida y el reloj no puede retroceder en el programador.

La capa está conectada al avance del reloj en el flujo de turno. La narración de consecuencias, la gestión de condiciones y las herramientas de administración de cronología siguen pendientes; no declarar el sistema completo hasta cubrir esos puntos.
