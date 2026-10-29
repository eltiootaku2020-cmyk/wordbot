# Informe de fiabilidad — 29 de octubre de 2026

## Objetivo

Mejorar continuidad y recuperación del gestor local sin convertir ChatGPT/Gemini web en la base del juego ni requerir llamadas de API. El principio se mantiene: la IA propone narración y cambios; SQLite y el validador local deciden qué se conserva.

## Estado verificado del repositorio

- Rama organizada de desarrollo: `docs/historias-organizadas`.
- La rama `main` conserva únicamente `.gitignore`; el prototipo y la documentación están en `docs/historias-organizadas`.
- Historial de CI: recuperación de turnos, 71 pruebas; destinos contradictorios, 72; movimientos de PNJ fuera de escena, 73; evidencia afirmativa, 75; continuidad extendida, 79. La CI posterior al PR #6 aprobó 81 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505. Esto no sustituye la validación manual en Windows.
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

Las correcciones integradas incluyen recuperación tras reinicio, respaldo aislado por sesión, destinos contradictorios, movimientos fuera de escena, evidencia afirmativa, restauración con rollback y compatibilidad de presencia histórica. La CI posterior al PR #6 aprobó 81 pruebas Python y sintaxis JavaScript correctamente (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505). No se hicieron llamadas reales a cuentas ChatGPT/Gemini ni a APIs.

## Trabajo restante para una primera versión fiable

1. [x] CI: 81 pruebas Python y sintaxis JavaScript aprobadas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505).
2. [x] Regresión de JSON truncado: el estado del juego no cambia; la respuesta corregida reutiliza el mismo turno.
3. [x] Regresión de acciones hipotéticas/preguntas, cambios narrativos contradictorios y propuestas sin evidencia afirmativa.
4. [x] Restauración exacta tras 100 turnos breves simulados: reinicializar SQLite, guardar copia, aplicar una mutación posterior, restaurar y comparar el estado, los mensajes y todas las tablas restaurables.
5. [x] Fallo de integridad durante restauración: la transacción se revierte; la API devuelve un 422 controlado y el estado activo permanece idéntico.
6. [ ] Validar manualmente la interfaz y el intercambio copiar/pegar en Windows/Chromium con ChatGPT web y Gemini web.
7. [ ] Ejecutar una campaña narrativa real de 50–100 intercambios con escenas privadas/grupales, decisiones, recursos y reinicio/restauración. La prueba de 100 turnos existente utiliza el proveedor simulado y no reemplaza este ensayo.
8. [x] Compatibilidad histórica de `session_presence` y restauración de backups sin `presence_status` (PR #6). [ ] Revisar mensajes/eventos históricos sin metadatos de audiencia.

No se considera terminado un hito por existir un archivo o una ficha: los criterios deben estar ligados a comportamiento verificable y a una prueba reproducible.

## Histórico de actualización — PR #5:

PR #5 fue integrado en `docs/historias-organizadas` (commit `90e8196331406f999ec42f1a4e5b2eb8f4282937`). La CI del PR aprobó 79 pruebas Python y la comprobación de sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884.

La prueba larga ahora comprueba la igualdad exacta de `/state`, mensajes y las tablas de sesión restaurables después de 100 turnos simulados, una reinicialización de SQLite, la creación de una copia, una mutación posterior y la restauración. Otra prueba modifica el esquema de una copia de forma que el archivo siga siendo una base SQLite legible pero incumpla una restricción de la base activa; la restauración se revierte por completo y devuelve 422. También se añadieron casos para JSON truncado, compras hipotéticas y cambios de relación contradictorios.

No sustituye la validación manual en Windows ni una campaña narrativa prolongada con un chat externo real.


## Última actualización — PR #6: compatibilidad de presencia histórica

PR #6 quedó integrado en `docs/historias-organizadas` con commit `8a08870b7e3cbba8a107a34a74bd947e919b9c8a`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/6. La CI posterior a la integración aprobó **81 pruebas Python** y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505).

La inicialización migra la tabla `session_presence` si una base antigua carece de `presence_status` o `updated_at`. Las filas y ubicaciones se conservan y el estado de presencia se normaliza respecto de `sessions.current_location`. La restauración también acepta backups cuya tabla de presencia no contiene `presence_status` y reconstruye el campo desde la ubicación guardada.

La cobertura está centrada en estos formatos históricos y no garantiza compatibilidad con todas las variantes posibles. Siguen pendientes la prueba manual del puente web en Windows/Chromium, mensajes/eventos antiguos sin metadatos de audiencia, restauración visual con vista previa y una campaña narrativa de 50–100 turnos con un chat externo real. La rama `main` no se modificó.
