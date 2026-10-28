# Estado general de los proyectos — continuidad entre chats

**Rama organizada de trabajo:** `docs/historias-organizadas`  
**Repositorio:** https://github.com/eltiootaku2020-cmyk/wordbot

## Regla principal

Trabajar desde la rama `docs/historias-organizadas` para los siguientes cambios. No mezclar archivos, personajes, poderes ni canon de proyectos diferentes. Las ramas de trabajo previas se conservan como respaldo; no borrarlas ni tratarlas como la carpeta organizada actual.

## Proyectos

### 1. Isekai sin Destino
- Carpeta: `proyectos/isekai-sin-destino/`
- Versión de configuración: v1.9 propuesta (pendiente de prueba); Lorebook ampliada con encuentros emergentes y seguimiento multidimensional de vínculos.
- Archivos: `CONFIG_LIGERA.md`, `CUADRO_REGLAS_PRIORITARIAS.md`, `LOREBOOK_MAESTRA.md`, `LOREBOOK_IMPORT.json`, `README.md`.
- Lorebook: 72 entradas.
- Cambios recientes: cuadro prioritario v1.9; reloj por seis bloques de cuatro horas; mini mapa progresivo que solo revela lo conocido por el protagonista; reloj con cabecera dinámica para que el saludo del Día 1 no se repita; encuentros aleatorios controlados; persistencia de estado de monstruos y PNJ; los compañeros conservan recuerdos; un monstruo muerto no reaparece como el mismo individuo sin causa; Eco mantiene usos y efectos por objetivo; se registran promesas, objetos y animales afectados por Eco/hipnosis; los vínculos incluyen sospechas, discusiones, amistad, respeto, deudas y conflictos, no solo romance; los compañeros solo reaccionan a hechos que presenciaron o les contaron, incluso si se enteran después.
- Persistencia práctica: el bot puede generar `/guardar`, pero SpicyChat no guarda por instrucciones un estado RPG externo. La partida necesita un punto de guardado copiado fuera del chat para recuperarla si el contexto se pierde.
- Diagnóstico añadido: `proyectos/isekai-sin-destino/SOLUCION_HISTORIAS_LARGAS.md`. SpicyChat no garantiza el estado exacto de un RPG a partir de prompts; se comparan procedimiento de guardado manual, SillyTavern para uso personal y una aplicación con base de datos por usuario.
- Pendiente: probar realmente la propuesta v1.9 en SpicyChat; comprobar los bloques de cuatro horas, el mini mapa, la regla de monstruos reaparecidos y el registro de promesas/Eco; decidir si se seguirá en SpicyChat o se probará una interfaz con resúmenes y recuperación.

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

Probar en SpicyChat el Isekai v1.8 propuesto, incluido el bloque prioritario de Personality. No crear una partida nueva hasta guardar cualquier progreso actual. Si el bot vuelve al Día 1, no aceptar ese reinicio: usar el último `[PUNTO DE GUARDADO]` copiado y reanudar desde allí. Registrar los resultados en la carpeta de Isekai antes de hacer más cambios.
