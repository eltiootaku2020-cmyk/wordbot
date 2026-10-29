# Informe de fiabilidad — 29 de octubre de 2026

## Objetivo

Mejorar continuidad y recuperación del gestor local sin convertir ChatGPT/Gemini web en la base del juego ni requerir llamadas de API. El principio se mantiene: la IA propone narración y cambios; SQLite y el validador local deciden qué se conserva.

## Estado verificado del repositorio

- Rama organizada de desarrollo: `docs/historias-organizadas`.
- La rama `main` conserva únicamente `.gitignore`; el prototipo y la documentación están en `docs/historias-organizadas`.
- La CI de recuperación aprobó 71 pruebas, la de destinos contradictorios 72 y la de movimientos fuera de escena 73 pruebas Python; las tres también pasaron la sintaxis JavaScript. Última ejecución: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40908949397. Esto no sustituye la validación manual en Windows.
- La suite existente incluye un escenario automatizado de 100 turnos breves con reinicialización de la base y copia/restauración; eso es una prueba de regresión local, no una simulación de todos los errores de una historia real.
- El modo ChatGPT/Gemini web es manual: preparar prompt, abrir el sitio, copiar y pegar una respuesta JSON. No automatiza el navegador, no lee la cuenta y no requiere clave API.

## Defectos corregidos en esta rama

### 1. Una copia de una partida no debe depender de otra partida

El respaldo consultaba si existía cualquier mensaje `processing` en la base, sin filtrar por el identificador de la partida. Un turno activo en la partida B podía bloquear la copia de la partida A. La consulta ahora se limita a `session_id`.

### 2. Recuperación después de un cierre inesperado

Un cierre mientras la IA generaba una respuesta podía dejar el mensaje de usuario como `processing`. Ese estado bloqueaba nuevos turnos; la interfaz además ocultaba el mensaje fallido, haciendo difícil recuperar lo que el usuario había escrito.

Al iniciar la aplicación, los turnos de usuario que sigan marcados como `processing` pasan a `failed`, conservando texto, destinatario y metadatos. La interfaz los muestra como interrumpidos y ofrece reintentarlos. No se inventa una narración ni se aplica ningún cambio de estado durante la recuperación.

Para ChatGPT/Gemini web se prepara un prompt nuevo y se pide pegar una respuesta nueva, porque la aplicación no guarda ni puede reconstruir una respuesta que solo existía en el chat externo. Para proveedores automáticos, el reintento reutiliza la clave de solicitud guardada para evitar duplicar operaciones.

### 3. Movimientos contradictorios y personajes fuera de escena\n\nUna respuesta podía proponer varios movimientos del mismo PNJ con distintos `event_ref`; cada movimiento superaba la detección de duplicados y la ubicación final dependía del orden de la lista. Ahora cualquier PNJ con más de un movimiento propuesto en el mismo turno queda sin mover y todas esas propuestas quedan pendientes.\n\nTambién se bloquea el movimiento automático de un PNJ que ya está ausente de la escena activa o cuya ubicación registrada no coincide con la escena. El narrador puede dejar constancia de una propuesta, pero no teletransportarlo a la escena del protagonista. Las pruebas de regresión cubren ambos escenarios.\n\n## Criterios que se mantienen

- Los mensajes breves como «sí», «no», «sigo» o «mira» son entradas válidas y no requieren un prompt largo.
- Los errores de JSON, claves duplicadas y campos extra deben rechazarse antes de cambiar el estado.
- Un prompt viejo no debe poder aplicarse después de que la partida cambie.
- Las compras, recursos y usos de poderes deben validarse y aplicarse una sola vez.
- Los datos de cada mundo y partida deben mantenerse separados.
- Rumores, propuestas y cambios de alto impacto no se convierten silenciosamente en canon confirmado.

## Validación

Las correcciones integradas incorporan pruebas para recuperación tras reinicio, respaldo aislado por sesión, destinos contradictorios y movimientos fuera de escena. CI completada correctamente: 73 pruebas Python aprobadas y sintaxis JavaScript correcta (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40908949397). No se hicieron llamadas reales a cuentas ChatGPT/Gemini ni a APIs porque no eran necesarias para estos arreglos.

## Trabajo restante para una primera versión fiable

1. [x] CI aprobada: 73 pruebas Python y sintaxis JavaScript. 2. Ampliar pruebas de restauración y coherencia narrativa; Windows sigue siendo validación manual opcional.
2. Ampliar los tests automatizados de respuestas truncadas, JSON mal formado, mensajes cortos, typos de comandos, fallos de restauración y cambios concurrentes.
3. Confirmar de manera automatizada el escenario de 50–100 turnos tras reiniciar y restaurar, incluyendo la igualdad de estado antes y después.
4. Dejar Windows/Chromium y la prueba de intercambio manual real como validación de interfaz opcional para el usuario, no como bloqueo para continuar la ingeniería.
5. Las API oficiales y la métrica de tokens/coste permanecen opcionales; solo aplican si se decide usar esas API.

No se considera terminado un hito por existir un archivo o una ficha: los criterios deben estar ligados a comportamiento verificable y a una prueba reproducible.
