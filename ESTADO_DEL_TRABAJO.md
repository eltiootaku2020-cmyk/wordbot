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
- CI de la rama de corrección: 71 pruebas Python y sintaxis JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40906597871. Incluye el puente manual ChatGPT/Gemini web y el rechazo de contexto desactualizado. La corrección ya fue integrada mediante PR #1 en `docs/historias-organizadas`; no valida Windows manual ni campaña narrativa real.
- Pendiente: prueba manual en Windows con ChatGPT/Gemini web; compatibilidad de datos históricos/cambios de presencia; exportación/restauración visual; campaña de 50–100 intercambios. Las llamadas API reales y su medición de tokens/coste son opcionales.
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
- Estado: v0.1 con código real en desarrollo; la documentación anterior que decía «solo documentación» quedó obsoleta. Las cifras 32/38 son históricas; la CI más reciente de la rama de corrección aprobó 71 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40906597871. No es una validación manual de Windows.
- Stack: Python + FastAPI, HTML/CSS/JavaScript ligero en Chromium, SQLite y proveedores simulados/OpenAI/Gemini.
- Ya existe: base local, interfaz, importación del JSON real de Isekai v1.16 (76 entradas), creación de mundos/partidas, reparto/inventario, mensajes/eventos, audiencia scene/private, filtrado por destinatario/testigos, inspector de contexto Lorebook y libro de recursos con compras validadas.
- Referencias: `INVESTIGACION_REFERENCIAS.md`; decisiones ADR-001 a ADR-014 en `DECISIONES_TECNICAS.md`; prioridades P0–P4 en `ROADMAP_IMPLEMENTACION.md`.
- **Privacidad por audiencia implementada:** selector escena/grupo o privado, metadatos de audiencia y filtro de mensajes/eventos por destinatario/testigos; el inspector explica las inclusiones/exclusiones. CI actual de la rama de corrección: 71 pruebas Python y sintaxis JavaScript aprobadas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40906597871). Sigue pendiente probar manualmente Windows y tratar cambios de presencia históricos.
- Otros pendientes prioritarios: prueba manual Windows del chat web; rollback al editar/regenerar más escenarios; compatibilidad de cambios de presencia antiguos; prueba de 50–100 intercambios y restauración. Llamadas API reales son opcionales.
- No hay que enviar el Lorebook completo cada turno ni extraer respuestas automáticamente de la página web. En el modo manual previsto, el usuario copia un prompt compacto a ChatGPT/Gemini y pega la respuesta; el programa la valida y guarda solo los cambios aceptados. Las llamadas API son opcionales y están separadas del chat web.
- Rama de trabajo: `docs/historias-organizadas`. La rama literal `main` de este repositorio sigue sin las carpetas organizadas de mundos/Lorebooks; no mezclar ni mover ramas sin una tarea explícita.

### Actualización del gestor local — 29-10-2026
- Las referencias de 32/38 pruebas son históricas; la ejecución más reciente de la rama de corrección aprobó 71 pruebas Python y sintaxis JS: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40906597871.
- Referencias web actuales: Chronicler (ACL de conocimiento por personaje + inspector), Open Dungeon (app local SQLite con edición/reintento), Gamentic (FastAPI/SQLite con herramientas validadas pero requisitos de hardware superiores), Openovel (narración separada del mantenimiento), AI Adventure (historial SQLite, validación de eventos, undo/ramas y checkpoints) y documentación World Info de SillyTavern.
- Código: privacidad scene/private; Lorebook de ocho entradas máximo y presupuesto configurable de 500–12.000 caracteres (4.500 por defecto), ocho entradas máximas e inspector de disparadores/inclusión/exclusión; inventario y libro de recursos por partida; compras con saldo transaccional; snapshots preturno y undo del último turno completado con auditoría.
- Monedas de Isekai empiezan en cero; compra con coste positivo y saldo suficiente descuenta dinero y añade objeto en la misma transacción; saldo insuficiente no cambia ninguno. Los cambios ambiguos siguen pendientes.
- Pendiente siguiente: ensayo manual en Windows con el chat web normal; compatibilidad de datos antiguos y entradas/salidas de escena; campaña de 50–100 turnos y restauración de backup. Tokenización/coste API solo si se usa la modalidad API.
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

Continuar el gestor local en este orden: (1) probar manualmente en Windows el puente de copiar/pegar con el chat web normal de ChatGPT y Gemini; (2) comprobar la protección contra contexto desactualizado, las conversaciones privadas y el undo; (3) revisar compatibilidad de datos históricos, exportación/restauración y cambios de presencia; (4) realizar una campaña de 50–100 turnos con reinicio y restauración. Las llamadas reales y medición de tokens/coste de las APIs son opcionales, separadas de las cuentas de chat web. Mantener en paralelo las pruebas de SpicyChat documentadas en la carpeta de Isekai. No declarar «Done» un hito que solo tenga documentación o una prueba simulada.


## Corrección importante: ChatGPT/Gemini web, no necesariamente API

El usuario aclaró que al decir IA se refiere al chat normal de ChatGPT o Gemini en sus páginas web, con su cuenta, no necesariamente a los endpoints API. No asumir que su objetivo primario son llamadas API.

**Implementación en la rama `docs/historias-organizadas`:**
- El selector ofrece ChatGPT web (manual) y Gemini web (manual), además del modo simulado y los proveedores API separados.
- `POST /api/sessions/{session_id}/manual-prompt` prepara un prompt con el contexto compacto de la partida y el esquema JSON del narrador.
- La interfaz permite copiar el prompt, abrir el sitio seleccionado y pegar la respuesta JSON. El backend la valida y después ejecuta las mismas validaciones de estado/inventario/recursos antes de guardar.
- No se automatizan login, envío de mensajes, lectura del DOM ni extracción automática de respuestas. El usuario revisa qué datos del juego pega al proveedor.
- Los adaptadores API siguen disponibles opcionalmente y no deben confundirse con la suscripción/cupo de chat web.

**Verificación actual de esta corrección:** CI — 71 pruebas Python y comprobación de sintaxis JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40906597871. No es una prueba real del navegador ni de una cuenta ChatGPT/Gemini.

**Pendiente:** prueba manual en Windows con ChatGPT web y Gemini web; comprobar el intercambio JSON en ambos; probar 50–100 turnos, reinicio y restauración. El chat web manual no tiene medida automática de tokens/coste. No revertir este enfoque a automatización del navegador sin nueva investigación y evaluación de políticas.


### Protección adicional del puente manual

Cada prompt preparado devuelve una huella SHA-256 del contexto exacto. Al pegar la respuesta, el servidor reconstruye el contexto actual y lo compara antes de aceptar el turno; si la partida cambió entre ambas acciones, rechaza la respuesta y pide volver a preparar el prompt. Esta comprobación evita aplicar una escena basada en un estado antiguo. Está cubierta por una prueba de CI.
