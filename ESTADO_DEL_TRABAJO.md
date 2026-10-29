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
- Preset Isekai v1.19: botón dedicado carga las 77 entradas del JSON de Lorebook, el reparto inicial y cinco objetos, y abre una sesión independiente por partida.
- CI más reciente de fiabilidad: 79 pruebas Python y sintaxis JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884. Incluye recuperación tras reinicio, reintentos idempotentes, evidencia afirmativa, JSON truncado, contradicciones narrativas y restauración exacta tras 100 turnos simulados. PR #1–#5 ya están integrados en `docs/historias-organizadas`; no valida Windows manual ni una campaña narrativa con un modelo externo.
- Pendiente: prueba manual en Windows con ChatGPT/Gemini web; compatibilidad de datos históricos/cambios de presencia; exportación/restauración visual; campaña de 50–100 intercambios. Las llamadas API reales y su medición de tokens/coste son opcionales.
- Documentos: `INVESTIGACION_REFERENCIAS.md`, `DECISIONES_TECNICAS.md`, `ROADMAP_IMPLEMENTACION.md`, `ARQUITECTURA.md`, `CONTRATO_RESPUESTA_IA.md`, `ESQUEMA_LOCAL.md`, `PRUEBAS_DE_ACEPTACION.md`.
- Ubicación de trabajo: rama `docs/historias-organizadas`. La rama literal `main` aún no contiene las carpetas organizadas de mundos.


### Actualización Isekai v1.19 (2026-10-29)
- Percentages include previous/current value, Δ in percentage points, SUBE/BAJA/SIN CAMBIO and cause. No registrado is not 0%, 50% or neutral.
- Natural proactive NPC dialogue: complete, contextual lines every 1–2 replies when someone has a reason; no fragments. Ivar can comment or sigh while ahead of the group.
- Objects and creatures are distinct; orders retain last location and remain pending/unknown until confirmed.
- Eco on trees stays a sensory discovery; mechanism, reach, cost, duration and counter remain unconfirmed.
- Master Lorebook's outdated 08:03/08:15 examples were replaced with four-hour blocks.
- Automated audit passed on v1.19 with 659 checks, including exact master-Lorebook/JSON and Personality synchronization: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935499563. Manual SpicyChat import and real roleplay tests remain pending.

### 1. Isekai sin Destino
- Carpeta: `proyectos/isekai-sin-destino/`
- Revisión: v1.19; porcentajes con tendencia y causa, iniciativa de diálogo reforzada, esquema de objetos/órdenes/Eco actualizado y Lorebook/JSON sincronizados con 77 entradas.
- Lorebook: Content <1.000 caracteres como margen conservador; keywords únicas tras normalizar mayúsculas/espacios.
- Cambios: bloques de 4 horas; mapa progresivo; encuentros sociales abiertos; PNJ conocen solo hechos presenciados/contados; diálogo proactivo; vínculos multidimensionales; porcentajes/delta precisos; esquema cerrado para habilidades, intereses, sospechas, conocimientos, órdenes, objetos y usos de Eco.
- Porcentajes: intensidad 0–100, no probabilidad; No registrado ≠ 0%; Δ en puntos porcentuales; Δ0 = sin cambio por ese hecho.
- Inventario inicial unificado: ropa corriente, pañuelo gastado, bolsita vacía y cordel corto; sin dinero, comida, agua, armas ni mochila. Los objetos del catálogo son posibilidades, no posesiones.
- Guardado: cada 5–7 intercambios y tras cambios importantes; Free requiere partes por el máximo de 180 tokens por respuesta. SpicyChat no guarda estado externo mediante instrucciones de texto.
- Prototipo local: el preset importa el JSON y debe devolver 77 entradas. La prueba de conteo, tamaño y unicidad de keywords pasó en [CI](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40930336007); los cambios posteriores han sido documentales.
- Pendiente: importación en SpicyChat y prueba manual del roleplay; prueba manual de la app en Windows.

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
- Estado: v0.1 con código real en desarrollo; la documentación anterior que decía «solo documentación» quedó obsoleta. Las cifras 32/38/71/75 son históricas; la CI más reciente aprobó 79 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884. No es una validación manual de Windows.
- Stack: Python + FastAPI, HTML/CSS/JavaScript ligero en Chromium, SQLite y proveedores simulados/OpenAI/Gemini.
- Ya existe: base local, interfaz, importación del JSON real de Isekai v1.16 (77 entradas), creación de mundos/partidas, reparto/inventario, mensajes/eventos, audiencia scene/private, filtrado por destinatario/testigos, inspector de contexto Lorebook y libro de recursos con compras validadas.
- Referencias: `INVESTIGACION_REFERENCIAS.md`; decisiones ADR-001 a ADR-014 en `DECISIONES_TECNICAS.md`; prioridades P0–P4 en `ROADMAP_IMPLEMENTACION.md`.
- **Privacidad por audiencia implementada:** selector escena/grupo o privado, metadatos de audiencia y filtro de mensajes/eventos por destinatario/testigos; el inspector explica las inclusiones/exclusiones. CI actual de fiabilidad: 79 pruebas Python y sintaxis JavaScript aprobadas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884). Sigue pendiente validar visualmente Windows y cubrir cambios históricos de presencia.
- Otros pendientes prioritarios: prueba manual Windows del chat web; rollback al editar/regenerar más escenarios; compatibilidad de cambios de presencia antiguos; prueba de 50–100 intercambios y restauración. Llamadas API reales son opcionales.
- No hay que enviar el Lorebook completo cada turno ni extraer respuestas automáticamente de la página web. En el modo manual previsto, el usuario copia un prompt compacto a ChatGPT/Gemini y pega la respuesta; el programa la valida y guarda solo los cambios aceptados. Las llamadas API son opcionales y están separadas del chat web.
- Rama de trabajo: `docs/historias-organizadas`. La rama literal `main` de este repositorio sigue sin las carpetas organizadas de mundos/Lorebooks; no mezclar ni mover ramas sin una tarea explícita.

### Actualización del gestor local — 29-10-2026
- Las referencias de 32/38/71/75 pruebas son históricas; la ejecución más reciente aprobó 79 pruebas Python y sintaxis JS: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884.
- Referencias web actuales: Chronicler (ACL de conocimiento por personaje + inspector), Open Dungeon (app local SQLite con edición/reintento), Gamentic (FastAPI/SQLite con herramientas validadas pero requisitos de hardware superiores), Openovel (narración separada del mantenimiento), AI Adventure (historial SQLite, validación de eventos, undo/ramas y checkpoints) y documentación World Info de SillyTavern.
- Código: privacidad scene/private; Lorebook de ocho entradas máximo y presupuesto configurable de 500–12.000 caracteres (4.500 por defecto), ocho entradas máximas e inspector de disparadores/inclusión/exclusión; inventario y libro de recursos por partida; compras con saldo transaccional; snapshots preturno y undo del último turno completado con auditoría.
- Monedas de Isekai empiezan en cero; compra con coste positivo y saldo suficiente descuenta dinero y añade objeto en la misma transacción; saldo insuficiente no cambia ninguno. Los cambios ambiguos siguen pendientes.
- Pendiente siguiente: ensayo manual en Windows con el chat web normal; compatibilidad de datos antiguos y entradas/salidas de escena; campaña narrativa de 50–100 turnos con un modelo real. La suite automatizada ya comprueba 100 turnos breves simulados y restauración exacta de la copia. Tokenización/coste API solo si se usa la modalidad API.
- No se considera terminado hasta que las pruebas de campaña larga y restauración pasen.

## Separación de ramas

- Rama organizada: `docs/historias-organizadas` — contiene los dos proyectos en carpetas separadas y debe usarse para nuevos cambios.
- Rama previa de Isekai: `docs/isekai-spicychat-lorebook` — respaldo de la línea de trabajo anterior, sin borrar.
- Rama previa de DanMachi: `docs/danmachi-spicychat` — respaldo de la línea de trabajo anterior, sin borrar.

### Histórico: Isekai v1.15 (superado por v1.19)
- Añadido el descubrimiento de Eco en árboles como sensación interna, no visual, con límites de prueba y parámetros desconocidos explícitos.
- Añadido inventario inicial limitado (pañuelo gastado, bolsita vacía, cordel corto); el resto del catálogo sigue siendo posibilidades, no regalos automáticos.
- Añadidas pautas para diálogo espontáneo completo de PNJ cercanos y metodología de identidad/estado/conocimiento/objetivos.
- Añadido documento de investigación con fuentes de SpicyChat, SillyTavern y diseño de PNJ.
- En la revisión histórica v1.15 se registró una Lorebook de 76 entradas; la revisión v1.18 incorporó 77 entradas y contadores de campos; v1.19 añade la auditoría automática y la corrección de coherencia del reloj.
- Añadidas instrucciones completas para `/estado` y `/guardar` al esquema cerrado.
- Pendiente de importar y probar en SpicyChat; no se declara validado.

## Próximo paso recomendado

Continuar el gestor local en este orden: (1) probar manualmente en Windows el puente de copiar/pegar con el chat web normal de ChatGPT y Gemini; (2) revisar compatibilidad de datos históricos, exportación/restauración y cambios de presencia; (3) realizar una campaña narrativa de 50–100 turnos con el chat web real, además de las pruebas de 100 turnos breves simulados y restauración exacta ya cubiertas por CI. Las llamadas reales y medición de tokens/coste de las APIs son opcionales, separadas de las cuentas de chat web. Mantener en paralelo las pruebas de SpicyChat documentadas en la carpeta de Isekai. No declarar «Done» un hito que solo tenga documentación o una prueba simulada.


## Corrección importante: ChatGPT/Gemini web, no necesariamente API

El usuario aclaró que al decir IA se refiere al chat normal de ChatGPT o Gemini en sus páginas web, con su cuenta, no necesariamente a los endpoints API. No asumir que su objetivo primario son llamadas API.

**Implementación en la rama `docs/historias-organizadas`:**
- El selector ofrece ChatGPT web (manual) y Gemini web (manual), además del modo simulado y los proveedores API separados.
- `POST /api/sessions/{session_id}/manual-prompt` prepara un prompt con el contexto compacto de la partida y el esquema JSON del narrador.
- La interfaz permite copiar el prompt, abrir el sitio seleccionado y pegar la respuesta JSON. El backend la valida y después ejecuta las mismas validaciones de estado/inventario/recursos antes de guardar.
- No se automatizan login, envío de mensajes, lectura del DOM ni extracción automática de respuestas. El usuario revisa qué datos del juego pega al proveedor.
- Los adaptadores API siguen disponibles opcionalmente y no deben confundirse con la suscripción/cupo de chat web.

**Verificación actual de continuidad y movimientos:** CI — 79 pruebas Python y comprobación de sintaxis JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884. No es una prueba real del navegador ni de una cuenta ChatGPT/Gemini.

**Pendiente:** prueba manual en Windows con ChatGPT web y Gemini web; comprobar el intercambio JSON en ambos; ejecutar una campaña narrativa real de 50–100 turnos. El reinicio y la restauración exacta ya tienen cobertura automatizada con proveedor simulado. El chat web manual no tiene medida automática de tokens/coste. No revertir este enfoque a automatización del navegador sin nueva investigación y evaluación de políticas.


### Protección adicional del puente manual

Cada prompt preparado devuelve una huella SHA-256 del contexto exacto. Al pegar la respuesta, el servidor reconstruye el contexto actual y lo compara antes de aceptar el turno; si la partida cambió entre ambas acciones, rechaza la respuesta y pide volver a preparar el prompt. Esta comprobación evita aplicar una escena basada en un estado antiguo. Está cubierta por una prueba de CI.


## Histórico: Isekai v1.16 / Lorebook v1.17 (superado por v1.19)
- Personality incorpora foco narrativo y movimiento/acción de PNJ o entorno cada 1–2 respuestas, sin controlar al protagonista.
- Guardado completo en varias partes para respetar el límite de 180 tokens por respuesta en Free. Mantiene cronología causal de hitos aún relevantes y los 3–5 sucesos recientes por separado.
- Nuevo segmento de registro de Eco por uso: intención/objetivo/reacción/resultado/efectos por eje/Δ en puntos/testigos/coste y duración si se conocen.
- El efecto deseado no se asume como resultado; miedo y obediencia son ejes separados; capacidades de Eco vegetal/animal continúan abiertas hasta confirmarse.
- Validación pendiente dentro de SpicyChat; GitHub no instala automáticamente las modificaciones.

## Actualización de fiabilidad — 29-10-2026: evidencia de acción afirmativa

- Integrado mediante PR #4 en la rama docs/historias-organizadas; commit de integración: 304dd3ae73b74c32d5469d1b27a00905f8899338. La rama literal main no se modificó.
- Corregido un defecto de autorización: la descripción generada por el narrador ya no puede servir como prueba suficiente de que el protagonista compró o recogió un objeto, ingresó o gastó recursos o usó Eco. La evidencia debe estar en el mensaje actual del usuario, ser afirmativa y mencionar el objeto, recurso u objetivo aplicable.
- Las preguntas, negaciones, intenciones hipotéticas y acciones contrastantes se separan antes de autorizar el cambio. Por ejemplo, «No compro la manzana pero pago la posada» permite validar el pago de la posada, no adquirir la manzana.
- Las propuestas sin evidencia suficiente quedan pendientes de revisión; los cambios de relación asociados a un poder no confirmado tampoco se aplican.
- CI verificada: 75 pruebas Python aprobadas y comprobación de sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40928659012. Hubo una advertencia no bloqueante de compatibilidad httpx/Starlette y otra por la retirada de Node.js 20 en acciones de CI.
- Alcance no validado: aún faltan pruebas manuales en Windows con ChatGPT/Gemini web y la campaña de 50–100 turnos con reinicio y restauración. No se hicieron llamadas reales a cuentas web ni a APIs.
- Siguiente prioridad identificada entonces (completada en parte por PR #5): pruebas de respuestas truncadas, instrucciones ambiguas, contradicciones del narrador y comparación exacta de estado después de una secuencia larga. La siguiente actualización registra esos resultados.

## Actualización de fiabilidad — 29-10-2026: regresiones de continuidad extendida

- PR #5 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/5. Commit de integración: `90e8196331406f999ec42f1a4e5b2eb8f4282937`. La rama literal `main` sigue intacta.
- CI verificada: **79 pruebas Python aprobadas** y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40932636884.
- La prueba manual de reintento utiliza ahora JSON truncado, confirma que no cambia el estado del juego y verifica que la respuesta corregida reutiliza el mismo turno sin duplicarlo.
- Se añadieron pruebas para una compra formulada como hipótesis/pregunta, dos cambios contradictorios de amistad propuestos por el narrador y un fallo de restricción durante la restauración.
- La campaña automatizada de 100 turnos breves ahora reinicializa SQLite, crea una copia, introduce una mutación posterior, restaura y compara el estado, los mensajes y todas las tablas de sesión restaurables. Esta prueba usa el proveedor simulado; no equivale a una campaña narrativa con ChatGPT/Gemini reales.
- Si una fila de copia no cumple las restricciones de la base activa, la transacción se revierte y la API devuelve un error controlado; la prueba comprueba que el estado anterior permanece idéntico.
- Pendiente: ensayo manual en Windows/Chromium con los chats web reales, compatibilidad histórica de datos y campaña narrativa prolongada. Las llamadas reales a las API siguen siendo opcionales.
