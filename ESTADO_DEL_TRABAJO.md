# Estado general de los proyectos — continuidad entre chats

**Rama organizada de trabajo:** `docs/historias-organizadas`  
**Repositorio:** https://github.com/eltiootaku2020-cmyk/wordbot

## Regla principal

Trabajar desde la rama `docs/historias-organizadas` para los siguientes cambios. No mezclar archivos, personajes, poderes ni canon de proyectos diferentes. Las ramas de trabajo previas se conservan como respaldo; no borrarlas ni tratarlas como la carpeta organizada actual.

## Proyectos

### 0. Gestor local de canon, Lorebooks y continuidad
- Carpeta de diseño: `proyecto/`; código inicial: `proyecto/app/`.
- Estado: prototipo v0.1 implementado parcialmente; no es todavía una aplicación final.
- Stack: Python/FastAPI, HTML/CSS/JavaScript para Chromium, SQLite, narrador simulado y adaptadores iniciales OpenAI/Gemini.
- Flujo de ejemplo: «Hola, linda» dirigido a Maelis produce narración + evento + propuesta de cambio; la confianza queda pendiente si no existe valor inicial confirmado.
- Preset Isekai v1.16: botón dedicado carga las 76 entradas del JSON de Lorebook, los cinco aventureros, protagonista, cinco objetos iniciales y una nueva sesión cada vez, sin mezclar estado entre partidas.
- CI: 28 pruebas aprobadas el 29-10-2026, más comprobación sintáctica de JavaScript: [ejecución](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40873768030). Incluye privacidad por audiencia, inspector Lorebook, operaciones ordinarias de inventario y libro de recursos/compras. No valida proveedor real ni Windows.
- Pendiente: prueba manual en Windows; llamadas API reales; validación completa de movimiento/inventario; exportación/restauración visual; prueba de 50–100 intercambios.
- Documentos: `INVESTIGACION_REFERENCIAS.md`, `DECISIONES_TECNICAS.md`, `ROADMAP_IMPLEMENTACION.md`, `ARQUITECTURA.md`, `CONTRATO_RESPUESTA_IA.md`, `ESQUEMA_LOCAL.md`, `PRUEBAS_DE_ACEPTACION.md`.
- Ubicación de trabajo: rama `docs/historias-organizadas`. La rama literal `main` aún no contiene las carpetas organizadas de mundos.


### 1. Isekai sin Destino
- Carpeta: `proyectos/isekai-sin-destino/`
- Versión de configuración: Personality y esquema de continuidad v1.15; Lorebook revisada v1.16 (76 entradas, activadores depurados y contenido contaminado corregido). Importación y comportamiento real siguen pendientes de probar.
- Archivos: `CONFIG_LIGERA.md`, `CUADRO_REGLAS_PRIORITARIAS.md`, `REGISTRO_INTERNO_ESQUEMA.md`, `LOREBOOK_MAESTRA.md`, `LOREBOOK_IMPORT.json`, `README.md`.
- Lorebook: 76 entradas.
- Cambios recientes: cuadro prioritario v1.15; registro interno cerrado y porcentual con delta 0=sin cambio; reloj por seis bloques de cuatro horas; mini mapa progresivo que solo revela lo conocido por el protagonista; reloj con cabecera dinámica para que el saludo del Día 1 no se repita; encuentros aleatorios controlados; persistencia de estado de monstruos y PNJ; los compañeros conservan recuerdos; un monstruo muerto no reaparece como el mismo individuo sin causa; Eco mantiene usos y efectos por objetivo; se registran promesas, objetos y animales afectados por Eco/hipnosis; los vínculos incluyen sospechas, discusiones, amistad, respeto, deudas y conflictos, no solo romance; los compañeros solo reaccionan a hechos que presenciaron o les contaron, incluso si se enteran después; los PNJ cercanos pueden iniciar diálogo espontáneamente sin que el usuario los nombre o mire, con 1–2 intervenciones naturales por respuesta de grupo y sin frases sueltas.
- Registro interno: incluye habilidades demostradas, intereses/objetivos con fuente, sospechas con evidencia y conocimientos por PNJ; datos ausentes quedan como «No registrado», sin campos nuevos.
- Coste en caracteres v1.15: Personality 4468; Scenario 795; Greeting 687; Example Dialogue 1044 (verificar tokens con el contador del editor).
- Persistencia práctica: el bot puede generar `/guardar`, pero SpicyChat no guarda por instrucciones un estado RPG externo. La partida necesita un punto de guardado copiado fuera del chat para recuperarla si el contexto se pierde.
- El plan Free tiene 4.096 tokens de contexto compartidos y aproximadamente 740 tokens disponibles para Lorebook activada (según documentación oficial, cifras sujetas a cambios); revisar el contador del editor. Las entradas nuevas permanecen compactas y activadas por palabras clave.
- Diagnóstico añadido: `proyectos/isekai-sin-destino/SOLUCION_HISTORIAS_LARGAS.md`. SpicyChat no garantiza el estado exacto de un RPG a partir de prompts; se comparan procedimiento de guardado manual, SillyTavern para uso personal y una aplicación con base de datos por usuario.
- Pendiente: probar la Lorebook v1.16 en SpicyChat; comprobar los bloques de cuatro horas, el mini mapa, la regla de monstruos reaparecidos y el registro de promesas/Eco; decidir si se seguirá en SpicyChat o se probará una interfaz con resúmenes y recuperación.

### 2. DanMachi
- Carpeta: `proyectos/danmachi/`
- Versión propuesta: v0.2 — Orario durante los últimos años de la Edad Oscura, antes del Gran Conflicto de los Siete Días. El intervalo exacto sigue pendiente.
- Archivos base actualizados: `SPICYCHAT_CONFIG.md`, `LOREBOOK_ENTRIES.md`, `DECISIONES_Y_CONTINUIDAD.md`, `PRUEBAS_DE_COHERENCIA.md`, `README.md`.
- Documentos añadidos: `INVESTIGACION_EDAD_OSCURA.md` y `ESQUEMA_ESTADO_Y_GUARDADO.md`.
- Lorebook: 40 entradas breves, cada Content bajo 1.000 caracteres como margen conservador.
- Reparto/facciones: Astraea, Alise Lovell, Ryuu Lion, Gojouno Kaguya, Lyra y compañeras; Evilus, Apate, Alecto, Erebus, Alfia y Zald; referencias a Loki, Freya, Gremio, Rudra y al futuro incidente del piso 27.
- Memoria: esquema cerrado para habilidades demostradas, intereses/objetivos con fuente, sospechas/evidencia, conocimiento por PNJ, vínculos porcentuales con delta/causa, inventario, encuentros/testigos, órdenes y desviaciones del canon.
- Narración: encuentros abiertos; PNJ cercanos pueden hacer comentarios naturales, sin forzar que todos hablen. Solo reaccionan a hechos presenciados o contados.
- Protagonista: base provisional de adulto recién llegado, sin Familia/Falna/poder original confirmado; identidad y decisiones siguen pendientes.
- Pendiente: prueba en SpicyChat. No está instalado ni validado, y no hay JSON de importación porque el exportador no ha sido verificado.

### 3. Gestor local de canon, Lorebooks y continuidad
- Carpeta: `proyecto/`; aplicación prototipo: `proyecto/app/`.
- Estado: v0.1 con código inicial real; la documentación anterior que decía «solo documentación» quedó obsoleta. La última CI enlazada por el README del prototipo indica 28 pruebas automáticas aprobadas, no una validación completa en Windows.
- Stack: Python + FastAPI, HTML/CSS/JavaScript ligero en Chromium, SQLite y proveedores simulados/OpenAI/Gemini.
- Ya existe: base local, interfaz, importación del JSON real de Isekai v1.16 (76 entradas), creación de mundos/partidas, reparto/inventario, mensajes/eventos, audiencia scene/private, filtrado por destinatario/testigos, inspector de contexto Lorebook y libro de recursos con compras validadas.
- Referencias: `INVESTIGACION_REFERENCIAS.md`; decisiones ADR-001 a ADR-014 en `DECISIONES_TECNICAS.md`; prioridades P0–P4 en `ROADMAP_IMPLEMENTACION.md`.
- **Privacidad por audiencia implementada:** selector escena/grupo o privado, metadatos de audiencia y filtro de mensajes/eventos por destinatario/testigos. CI actual: 28 pruebas Python y sintaxis JavaScript aprobadas. Sigue pendiente explicar en inspector cada mensaje/evento incluido/excluido, cambios de presencia históricos y pruebas manuales de API/Windows.
- Otros pendientes prioritarios: política para autoaplicar operaciones cotidianas de bajo riesgo y retener las ambiguas/de alto impacto; inspector de activación Lorebook; rollback al editar/regenerar; prueba manual Windows; llamadas reales de OpenAI/Gemini; prueba de 50–100 intercambios y restauración.
- No hay que enviar el Lorebook completo cada turno ni extraer las respuestas de la página de ChatGPT de consumo. La IA debe recibir contexto mínimo a través de API oficial y proponer cambios que el programa valida y guarda.
- Rama de trabajo: `docs/historias-organizadas`. La rama literal `main` de este repositorio sigue sin las carpetas organizadas de mundos/Lorebooks; no mezclar ni mover ramas sin una tarea explícita.

### Actualización del gestor local — 29-10-2026
- CI validada: 28 pruebas Python y sintaxis de JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40873768030.
- Referencias web actuales: Chronicler (ACL de conocimiento por personaje + inspector), Open Dungeon (app local SQLite con edición/reintento y lanzador Windows), Gamentic (FastAPI/SQLite con herramientas validadas pero requisitos de hardware superiores), Openovel (narrador en primer plano y memoria en segundo plano) y documentación World Info de SillyTavern.
- Código: privacidad scene/private; Lorebook de ocho entradas máximo y 4.500 caracteres con inspector de disparadores; inventario de bajo riesgo validado; libro de recursos por partida; snapshots preturno y undo del último turno completado con auditoría.
- Monedas de Isekai empiezan en cero; compra con coste positivo y saldo suficiente descuenta dinero y añade objeto en la misma transacción; saldo insuficiente no cambia ninguno. Los cambios ambiguos siguen pendientes.
- Pendiente siguiente: prueba de idempotencia de compra en un turno API reintentado, rollback al editar/regenerar, inspector de mensajes/eventos, presupuesto configurable/tokenización y prueba manual Windows + APIs reales.
- No se considera terminado hasta que las pruebas de campaña larga y restauración pasen.

## Separación de ramas

- Rama organizada: `docs/historias-organizadas` — contiene los dos proyectos en carpetas separadas y debe usarse para nuevos cambios.
- Rama previa de Isekai: `docs/isekai-spicychat-lorebook` — respaldo de la línea de trabajo anterior, sin borrar.
- Rama previa de DanMachi: `docs/danmachi-spicychat` — respaldo de la línea de trabajo anterior, sin borrar.

### Actualización Isekai v1.15
- Añadido el descubrimiento de Eco en árboles como sensación interna, no visual, con límites de prueba y parámetros desconocidos explícitos.
- Añadido inventario inicial limitado (pañuelo gastado, bolsita vacía, cordel corto); el resto del catálogo sigue siendo posibilidades, no regalos automáticos.
- Añadidas pautas para diálogo espontáneo completo de PNJ cercanos y metodología de identidad/estado/conocimiento/objetivos.
- Añadido documento de investigación con fuentes de SpicyChat, SillyTavern y diseño de PNJ.
- Corregida la documentación maestra: bloques de cuatro horas, Lorebook de 76 entradas y contadores reales de campos.
- Añadidas instrucciones completas para `/estado` y `/guardar` al esquema cerrado.
- Pendiente de importar y probar en SpicyChat; no se declara validado.

## Próximo paso recomendado

Continuar el gestor local en este orden: (1) corregir y probar visibilidad de conocimientos por destinatario/testigos; (2) decidir qué cambios de bajo riesgo se aplican automáticamente y cuáles quedan pendientes; (3) añadir reversión de turnos editados/regenerados; (4) ejecutar la app en Windows y probar una llamada API real; (5) realizar una campaña de 50–100 turnos y reiniciar/restaurar la base para comprobar continuidad. Mantener en paralelo las pruebas de SpicyChat documentadas en la carpeta de Isekai. No declarar «Done» un hito que solo tenga documentación o una prueba simulada.
