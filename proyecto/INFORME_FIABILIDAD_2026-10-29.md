# Informe de fiabilidad — 29 de octubre de 2026

## Objetivo

Mejorar continuidad y recuperación del gestor local sin convertir ChatGPT/Gemini web en la base del juego ni requerir llamadas de API. El principio se mantiene: la IA propone narración y cambios; SQLite y el validador local deciden qué se conserva.

## Estado verificado del repositorio

- Rama organizada de desarrollo: `docs/historias-organizadas`.
- La rama `main` conserva únicamente `.gitignore`; el prototipo y la documentación están en `docs/historias-organizadas`.
- Historial de CI: recuperación de turnos, 71 pruebas; destinos contradictorios, 72; movimientos de PNJ fuera de escena, 73; evidencia afirmativa, 75; continuidad extendida, 79; presencia/backup histórico, 81; audiencia histórica, 82. La CI posterior al PR #8 aprobó 83 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271. Esto no sustituye la validación manual en Windows.
- La suite existente incluye un escenario automatizado de 100 turnos breves con reinicialización de la base y copia/restauración; eso es una prueba de regresión local, no una simulación de todos los errores de una historia real.
- El modo ChatGPT/Gemini web es manual: preparar prompt, abrir el sitio, copiar y pegar una respuesta JSON. No automatiza el navegador, no lee la cuenta y no requiere clave API.

## Defectos corregidos en esta rama

### 1. Una copia de una partida no debe depender de otra partida

El respaldo consultaba si existía cualquier mensaje `processing` en la base, sin filtrar por el identificador de la partida. Un turno activo en la partida B podía bloquear la copia de la partida A. La consulta ahora se limita a `session_id`.

### 2. Recuperación después de un cierre inesperado

Un cierre mientras la IA generaba una respuesta podía dejar el mensaje de usuario como `processing`. Ese estado bloqueaba nuevos turnos; la interfaz además ocultaba el mensaje fallido, haciendo difícil recuperar lo que el usuario había escrito.

Al iniciar la aplicación, los turnos de usuario que sigan marcados como `processing` pasan a `failed`, conservando texto, destinatario y metadatos. La interfaz los muestra como interrumpidos y ofrece reintentarlos. No se inventa una narración ni se aplica ningún cambio de estado durante la recuperación.

Para ChatGPT/Gemini web se prepara un prompt nuevo y se pide pegar una respuesta nueva, porque la aplicación no guarda ni puede reconstruir una respuesta que solo existía en el chat externo. Para proveedores automáticos, el reintento reutiliza la clave de solicitud guardada para evitar duplicar operaciones.

### 3. Movimientos contradictorios y personajes fuera de escena\n\nUna respuesta podía proponer varios movimientos del mismo PNJ con distintos `event_ref`; cada movimiento superaba la detección de duplicados y la ubicación final dependía del orden de la lista. Ahora cualquier PNJ con más de un movimiento propuesto en el mismo turno queda sin mover y todas esas propuestas quedan pendientes.\n\nTambién se bloquea el movimiento automático de un PNJ que ya está ausente de la escena activa o cuya ubicación registrada no coincide con la escena. El narrador puede dejar constancia de una propuesta, pero no teletransportarlo a la escena del protagonista. Las pruebas de regresión cubren ambos escenarios.\n\n## Corrección adicional: evidencia afirmativa del usuario

La revisión detectó que el validador podía unir el mensaje del usuario con la descripción generada por el narrador y usar ambos textos como prueba de que una compra, un hallazgo o un cambio de recurso habían ocurrido. Eso permitía que una respuesta narrativa se autorizara a sí misma.

Se corrigió el criterio local:

- Las compras y recogidas requieren una acción afirmativa del usuario que identifique el objeto.
- Los ingresos y gastos requieren una acción afirmativa que identifique el recurso.
- Preguntas, negaciones, formulaciones hipotéticas y acciones contrastantes se separan antes de validar.
- Un evento que no cuenta con evidencia suficiente queda pendiente; el narrador no puede convertir una propuesta en un hecho confirmado.
- Los usos de Eco deben tener una orden afirmativa aplicable al objetivo; los cambios de relación dependientes de un uso no confirmado también quedan pendientes.

Se añadieron dos pruebas de regresión: una combina una pregunta y negaciones sobre compra, hallazgo, gasto, ingreso y uso de Eco, aunque el narrador propone todos los cambios; la otra comprueba que «No compro la manzana pero pago dos monedas por la posada» no añade la manzana pero sí valida el pago independiente de la posada.

**Resultado CI verificado:** 75 pruebas Python aprobadas y sintaxis JavaScript correcta; una advertencia de compatibilidad de Starlette/httpx y otra por la retirada de Node.js 20 en acciones de CI, sin fallos de ejecución. Ejecución: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40928659012.

No se realizaron llamadas reales a APIs ni pruebas manuales de las páginas de ChatGPT/Gemini. Siguen pendientes la validación de interfaz en Windows y una campaña de 50–100 turnos con reinicio y restauración.

## Criterios que se mantienen

- Los mensajes breves como «sí», «no», «sigo» o «mira» son entradas válidas y no requieren un prompt largo.
- Los errores de JSON, claves duplicadas y campos extra deben rechazarse antes de cambiar el estado.
- Un prompt viejo no debe poder aplicarse después de que la partida cambie.
- Las compras, recursos y usos de poderes deben validarse y aplicarse una sola vez.
- Los datos de cada mundo y partida deben mantenerse separados.
- Rumores, propuestas y cambios de alto impacto no se convierten silenciosamente en canon confirmado.

## Validación

Las correcciones integradas incluyen recuperación tras reinicio, respaldo aislado por sesión, movimientos y acciones validados, restauración con rollback, compatibilidad de presencia/backup histórico, protección de audiencia heredada y aislamiento privado al deshacer/regenerar. La CI posterior al PR #8 aprobó 83 pruebas Python y sintaxis JavaScript correctamente (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271). No se hicieron llamadas reales a cuentas ChatGPT/Gemini ni a APIs.

## Trabajo restante para una primera versión fiable

1. [x] CI: 83 pruebas Python y sintaxis JavaScript aprobadas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271).
2. [x] Regresión de JSON truncado: el estado del juego no cambia; la respuesta corregida reutiliza el mismo turno.
3. [x] Regresión de acciones hipotéticas/preguntas, cambios narrativos contradictorios y propuestas sin evidencia afirmativa.
4. [x] Restauración exacta tras 100 turnos breves simulados: reinicializar SQLite, guardar copia, aplicar una mutación posterior, restaurar y comparar el estado, los mensajes y todas las tablas restaurables.
5. [x] Fallo de integridad durante restauración: la transacción se revierte; la API devuelve un 422 controlado y el estado activo permanece idéntico.
6. [ ] Validar manualmente la interfaz y el intercambio copiar/pegar en Windows/Chromium con ChatGPT web y Gemini web.
7. [ ] Ejecutar una campaña narrativa real de 50–100 intercambios con escenas privadas/grupales, decisiones, recursos y reinicio/restauración. La prueba de 100 turnos existente utiliza el proveedor simulado y no reemplaza este ensayo.
8. [x] Compatibilidad probada de presencia/backup y audiencia histórica: mensajes dirigidos limitados al destinatario conservado; eventos sin fuente ni testigos excluidos del contexto (PR #6/#7). [ ] Revisar variantes históricas adicionales.

No se considera terminado un hito por existir un archivo o una ficha: los criterios deben estar ligados a comportamiento verificable y a una prueba reproducible.

## Histórico de actualización — PR #5:

PR #5 fue integrado en `docs/historias-organizadas` (commit `90e8196331406f999ec42f1a4e5b2eb8f4282937`). La CI del PR aprobó 79 pruebas Python y la comprobación de sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884.

La prueba larga ahora comprueba la igualdad exacta de `/state`, mensajes y las tablas de sesión restaurables después de 100 turnos simulados, una reinicialización de SQLite, la creación de una copia, una mutación posterior y la restauración. Otra prueba modifica el esquema de una copia de forma que el archivo siga siendo una base SQLite legible pero incumpla una restricción de la base activa; la restauración se revierte por completo y devuelve 422. También se añadieron casos para JSON truncado, compras hipotéticas y cambios de relación contradictorios.

No sustituye la validación manual en Windows ni una campaña narrativa prolongada con un chat externo real.


## Última actualización — PR #6: compatibilidad de presencia histórica

PR #6 quedó integrado en `docs/historias-organizadas` con commit `8a08870b7e3cbba8a107a34a74bd947e919b9c8a`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/6. La CI posterior a la integración aprobó **81 pruebas Python** y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505).

La inicialización migra la tabla `session_presence` si una base antigua carece de `presence_status` o `updated_at`. Las filas y ubicaciones se conservan y el estado de presencia se normaliza respecto de `sessions.current_location`. La restauración también acepta backups cuya tabla de presencia no contiene `presence_status` y reconstruye el campo desde la ubicación guardada.

La cobertura está centrada en estos formatos históricos y no garantiza compatibilidad con todas las variantes posibles. Siguen pendientes la prueba manual del puente web en Windows/Chromium, mensajes/eventos antiguos sin metadatos de audiencia, restauración visual con vista previa y una campaña narrativa de 50–100 turnos con un chat externo real. La rama `main` no se modificó.


## Última actualización — PR #7: alcance conservador de eventos históricos

PR #7 quedó integrado en `docs/historias-organizadas` con commit `63710dd57577481c49a0bbb3bbeb8d232ad42375`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/7. La CI posterior a la integración aprobó **82 pruebas Python** y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743).

Cuando un mensaje anterior al sistema de audiencias conserva `recipient_entity_id`, el contexto mantiene ese límite y no se lo entrega a otro personaje. Para eventos, un vínculo a un mensaje fuente o testigos identificables permite aplicar las reglas existentes; si faltan ambos, el evento se excluye del contexto del modelo y el diagnóstico explica por qué. Los eventos no se borran y siguen disponibles para auditoría.

Esto complementa la migración de presencia y la restauración de backups antiguos del PR #6. No reemplaza la inspección manual de otras variantes de datos históricos ni las pruebas de Windows/Chromium y la campaña real de 50–100 turnos.


## Última actualización — PR #8: aislamiento privado a través de undo/regeneración

PR #8 quedó integrado en `docs/historias-organizadas` con commit `312c10ab4e2cdabc9e92a2842765c7f70fb0b0a5`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/8. La CI posterior a la integración aprobó **83 pruebas Python** y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271).

La regresión nueva realiza una conversación privada con Maelis que contiene un código distinguible, deshace el turno y lo regenera con el mismo identificador de solicitud. El contexto compartido de Ivar no revela ni el código de la narración ni el del evento antes de deshacer, después de deshacer o después de regenerar. El contexto privado de Maelis sí recupera el diálogo tras la regeneración. El evento anulado queda en el turno de auditoría con estado rechazado.

La prueba fortalece la interacción entre privacidad, testigos, undo y reintento idempotente, pero sigue usando un proveedor simulado. No sustituye la prueba manual de Windows/Chromium ni la campaña real de 50–100 turnos con ChatGPT/Gemini web.


## Última actualización — PR #9 y PR #10: rechazo de reintentos obsoletos

- PR #9 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/9. La CI aprobó 84 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940376539.
- PR #10 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/10; commit de integración `945a098aaaf65230fa5ff7b1618db7b1d70b322e`.
- La CI de PR #10 aprobó **86 pruebas Python**, una advertencia no bloqueante y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940906581.
- Error detectado: un turno anulado o fallido podía reintentarse después de que hubiese cambiado el estado del juego. El snapshot anterior podía aplicar un cambio cronológicamente obsoleto y hacer que un undo posterior revirtiese hechos más recientes.
- Corrección: la aplicación rechaza el reintento si hay turnos de usuario posteriores y compara el snapshot preturno con el estado mutable actual. Los snapshots ausentes, ilegibles o diferentes fallan de forma conservadora. Un reintento sigue siendo válido cuando no ocurrió ningún cambio y la instantánea sigue coincidiendo.
- Nuevas regresiones: reintento de turno anulado tras un turno nuevo; reintento de turno fallido tras turno nuevo; reintento fallido después de mutación del estado sin un turno narrativo posterior.
- Pendiente: Windows/Chromium y campaña manual real de 50–100 intercambios. La CI usa proveedor simulado y no comprueba una cuenta web real.


## Última actualización — PR #11: versión UI/JSON desincronizada

PR #11 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/11. Se encontró que el botón HTML mostraba `v1.16`, el README de la aplicación decía `v1.18`, pero el endpoint cargaba el archivo de Lorebook cuyo `description` y README de proyecto declaran `v1.19`. El programa cargaba el JSON real correctamente; era la etiqueta/documentación la que engañaba al usuario.

La etiqueta se actualizó a v1.19, el README de la app se corrigió y una prueba de regresión compara automáticamente la versión extraída del JSON con la del botón. CI aprobó **86 pruebas Python** y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934304. La auditoría independiente de Lorebook aprobó 659 comprobaciones: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934333.

La prueba detecta discrepancias entre texto estático y fuente de datos, pero no sustituye la inspección visual manual en Windows/Chromium.


## Última actualización — PR #12: no revertir aprobaciones posteriores con undo

PR #12 quedó integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/12; commit `6e2b940ea76b4d7a7ff36e5495674be9f13a0016`.

### Reproducción
Un primer turno dejó pendiente una propuesta de amistad para Maelis. Después se completó otro turno que avanzó el reloj a las 08:12. Al aprobar luego la propuesta del turno anterior, la relación quedó en 55 y su fila de cambio pasó a `accepted`. Antes de la corrección, deshacer el segundo turno devolvía éxito y restauraba 08:05, borrando la relación, mientras el registro seguía como aceptado. La prueba falló así contra el código anterior, demostrando la pérdida real del estado.

### Corrección
- Cada turno completado guarda en el JSON del snapshot una huella SHA-256 compacta del estado mutable posterior al turno; no requiere migración de esquema.
- Deshacer compara el estado actual con esa huella. Si hubo una aprobación, restauración u otra alteración del estado después del turno, responde 409 dentro de la transacción sin tocar la partida.
- Los snapshots antiguos sin huella conservan la opción de deshacer si no existe una aprobación aceptada posterior de otro turno; la huella se completa mientras la transacción tiene el bloqueo de escritura. Si se detecta una aprobación posterior, falla de forma conservadora y mantiene el estado.
- Los reintentos seguros siguen funcionando porque se compara el estado preturno sin mezclarlo con el metadato de la huella; tras regenerar correctamente se actualiza la huella posterior.
- CI PR #12: **87 pruebas Python aprobadas**, una advertencia no bloqueante y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768.

Pendiente: validación de interfaz Windows/Chromium y campaña externa larga real; la CI usa proveedor simulado.


## Actualización final de esta ronda — PR #13/#14 (29-10-2026)

### Nuevo control de concurrencia (PR #13, integrado)

Las operaciones de aprobar/rechazar propuestas de estado y eventos ahora se bloquean con HTTP 409 durante una generación activa en la misma sesión. Con esto se evita cambiar el estado confirmado o la visibilidad de hechos mientras el narrador usa un contexto obsoleto. CI post-merge: 88 pruebas Python y sintaxis JavaScript correctas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40944609761).

### Cancelación explícita durante espera del proveedor (PR #14, integrado)

Se detectó que `asyncio.CancelledError` puede escapar de los manejadores `except Exception`, dejando un turno persistido en `processing` si la tarea se cancela pero la aplicación continúa viva. El cambio captura esa cancelación alrededor de `provider.generate`, marca la solicitud como `failed` de forma transaccional, registra el incidente y vuelve a propagar la cancelación. La prueba conserva el texto original, verifica que el estado de juego no cambie y vuelve a intentar el mismo `request_id` una sola vez.

- PR #14: https://github.com/eltiootaku2020-cmyk/wordbot/pull/14.
- CI del HEAD de PR #14: **89 pruebas Python aprobadas** y sintaxis JavaScript correcta; queda una advertencia no bloqueante de Starlette/httpx: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40946590907.
- Nota de alcance: CI usa proveedor simulado. No constituye validación de Windows, Chromium ni de la cuenta real ChatGPT/Gemini. La campaña real de 50–100 turnos aún no se ejecutó.

### Comparación externa incorporada

La revisión de [Chronicler](https://github.com/yantrikos/chronicler), [AI Adventure](https://github.com/CaoRuiming/ai-adventure), [SillyTavern World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/) y [Open Dungeon](https://github.com/newideas99/open-dungeon) refuerza cuatro decisiones: ACL antes de recuperar memoria por relevancia, estado estructurado separado de la narración, Lorebook como contexto y no autoridad, y controles explícitos para reintentar/restaurar. Para copias consistentes se mantiene la [API de backup SQLite](https://www.sqlite.org/backup.html).

### Pendientes de aceptación

1. Ejecutar manualmente Windows/Chromium con ChatGPT web y Gemini web.
2. Ejecutar la campaña de 50–100 turnos reales, con cierres/reinicios, copias/restauración y checkpoints comparables del estado.
3. Probar escenarios de doble instancia y cancelaciones durante apagado total. Son riesgos candidatos para prueba; todavía no defectos confirmados.
4. Completar restauración visual con vista previa y revisar variantes históricas adicionales.

Word Bot no se declara terminado por el número de pruebas. El criterio de salida sigue siendo una campaña larga y recuperación real sin pérdida, duplicación ni canon inventado.
