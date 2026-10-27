# Estado general de los proyectos — continuidad entre chats

**Rama organizada de trabajo:** `docs/historias-organizadas`  
**Repositorio:** https://github.com/eltiootaku2020-cmyk/wordbot

## Regla principal

Trabajar desde la rama `docs/historias-organizadas` para los siguientes cambios. No mezclar archivos, personajes, poderes ni canon de proyectos diferentes. Las ramas de trabajo previas se conservan como respaldo; no borrarlas ni tratarlas como la carpeta organizada actual.

## Proyectos

### 1. Isekai sin Destino
- Carpeta: `proyectos/isekai-sin-destino/`
- Versión de configuración y Lorebook: v1.7.
- Archivos: `CONFIG_LIGERA.md`, `LOREBOOK_MAESTRA.md`, `LOREBOOK_IMPORT.json`, `README.md`.
- Lorebook: 72 entradas.
- Cambios recientes: Personality resumida; reloj con seis franjas diarias; cabecera dinámica para que el saludo del Día 1 no se repita; encuentros aleatorios controlados; persistencia de estado de monstruos y PNJ; los compañeros conservan recuerdos; un monstruo muerto no reaparece como el mismo individuo sin causa; Eco mantiene usos y efectos por objetivo.
- Persistencia práctica: el bot puede generar `/guardar`, pero SpicyChat no guarda por instrucciones un estado RPG externo. La partida necesita un punto de guardado copiado fuera del chat para recuperarla si el contexto se pierde.
- Diagnóstico añadido: `proyectos/isekai-sin-destino/SOLUCION_HISTORIAS_LARGAS.md`. SpicyChat no garantiza el estado exacto de un RPG a partir de prompts; se comparan procedimiento de guardado manual, SillyTavern para uso personal y una aplicación con base de datos por usuario.
- Pendiente: probar realmente la versión v1.7 en SpicyChat; comprobar si las seis franjas y la regla de monstruos reaparecidos funcionan; decidir si se seguirá en SpicyChat o se probará una interfaz con resúmenes y recuperación.

### 2. DanMachi
- Carpeta: `proyectos/danmachi/`
- Versión: v0.1, base inicial en desarrollo.
- Archivos: `SPICYCHAT_CONFIG.md`, `LOREBOOK_ENTRIES.md`, `DECISIONES_Y_CONTINUIDAD.md`, `PRUEBAS_DE_COHERENCIA.md`, `README.md`.
- Protagonista, origen, punto exacto del canon y posibles poderes originales: decisiones pendientes, no convertirlas en canon sin autorización.

## Separación de ramas

- Rama organizada: `docs/historias-organizadas` — contiene los dos proyectos en carpetas separadas y debe usarse para nuevos cambios.
- Rama previa de Isekai: `docs/isekai-spicychat-lorebook` — respaldo de la línea de trabajo anterior, sin borrar.
- Rama previa de DanMachi: `docs/danmachi-spicychat` — respaldo de la línea de trabajo anterior, sin borrar.

## Próximo paso recomendado

Probar en SpicyChat el Isekai v1.7 actualizado. No crear una partida nueva hasta guardar cualquier progreso actual. Si el bot vuelve al Día 1, no aceptar ese reinicio: usar el último `[PUNTO DE GUARDADO]` copiado y reanudar desde allí. Registrar los resultados en la carpeta de Isekai antes de hacer más cambios.
