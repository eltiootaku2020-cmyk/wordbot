# Roadmap de implementación — gestor local v0.1

La CI más reciente aprobó 87 pruebas Python en Linux/Python 3.12 y comprobó sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768.

## Fase 0 — Investigación y arquitectura
- [x] Revisar clientes de roleplay (SillyTavern, RisuAI, Agnai).
- [x] Revisar memoria persistente (LangGraph, Mem0, Graphiti).
- [x] Revisar Structured Outputs de OpenAI y salida estructurada de Gemini.
- [x] Revisar transacciones, WAL y copias de seguridad de SQLite.
- [x] Documentar restricciones de la página de consumo y facturación API.
- [x] Preparar las decisiones técnicas provisionales.
- [x] Crear y probar un flujo pequeño con proveedor simulado.
- [x] Cargar preset de Isekai sin Destino y validar las 77 entradas, reparto, inventario inicial y nueva sesión.
- [ ] Probar manualmente la instalación en Windows y revisar la interfaz en Chromium.

## Fase 1 — Esqueleto ejecutable
- [x] Crear estructura del paquete Python y configuración de entorno.
- [x] Crear SQLite y tablas iniciales.
- [x] Crear endpoints locales para mundo de prueba, entidades, partidas, mensajes, estado y Lorebook.
- [x] Crear página de chat mínima abierta en Chromium.
- [x] Crear configuración de proveedor en archivo .env fuera de Git; la UI no recibe claves.
- [x] Mostrar errores en la interfaz y guardar mensajes fallidos en la base; falta un sistema completo de logs técnicos.

Criterio de salida: se puede crear/seleccionar un mundo, enviar un mensaje simulado, guardar texto y reiniciar sin perderlo; aún no requiere un proveedor real.

## Fase 2 — Un turno completo con salida estructurada
- [x] Implementar narrador simulado y adaptadores API iniciales OpenAI/Gemini; llamadas reales aún no validadas.
- [x] Añadir modo manual para el chat web normal de ChatGPT/Gemini: preparar prompt local, copiar al sitio oficial, pegar la respuesta y validar JSON sin API key.
- [x] Enviar contexto reducido con estado, participantes, historial reciente y Lorebook relevante (máximo 8 entradas y presupuesto fijo de 4.500 caracteres de Lorebook).
- [x] Recibir narración, eventos y cambios propuestos en un contrato Pydantic/JSON.
- [x] Validar estructura, entidades y evento fuente; la validación semántica completa sigue pendiente.
- [x] Guardar mensajes, eventos y cambios aceptados/pendientes/rechazados en SQLite.
- [x] Implementar clave de idempotencia a nivel de solicitud y reutilizar la respuesta guardada en un reintento.

Criterio de salida: el caso «Hola, linda» genera una escena y un registro del intercambio, sin requerir un bloque de guardado en el chat.

## Fase 3 — Estado esencial del juego
- [x] Guardar día, hora, ubicación y personajes presentes; reloj básico y /salto explícito implementados.
- [x] Guardar inventario con cantidad, condición, portador y ubicación; consumo, condición, soltar, transferir, recoger pilas registradas y hallazgos/regalos de bajo riesgo pasan validaciones locales. Compras se integran con libro de recursos y saldo.
- [x] Guardar relaciones por eje y su motivo; cambios sin base confirmada quedan pendientes.
- [x] Guardar usos de poderes y aplicar el límite humano de Eco al aprobar un uso; faltan pruebas de casos límite.
- [x] Registrar eventos, testigos y fuente; el conocimiento individual requiere más desarrollo.
- [x] Validaciones locales de acciones, movimientos, compras, recursos y usos de habilidades; cubiertas por pruebas automáticas, con propuestas ambiguas o contradictorias dejadas pendientes.

Criterio de salida: un cambio sólo se aplica si tiene una causa válida; el mismo mensaje no puede descontar un poder dos veces.

## Fase 4 — Lorebook y recuperación
- [x] Importar Lorebook JSON compatible con SpicyChat; exportación de mundos y partidas sigue pendiente.
- [x] Activar fichas por palabras clave, nombres de participantes y lugar; falta ampliar y probar selección.
- [ ] Resolver conflictos de prioridades y estados canon/pendiente/rumor.
- [ ] Añadir búsqueda de eventos/diálogos antiguos.
- [ ] Definir un presupuesto de tokens configurable y mostrar qué se envió al modelo.

Criterio de salida: el programa envía solo el lore necesario y no convierte un rumor en hecho.

## Fase 5 — Fiabilidad y recuperación
- [x] Crear copia SQLite consistente.
- [x] Snapshot preturno automático enlazado a turno.
- [x] Undo del último turno completado desde la interfaz/API: restaura estado y conserva la versión anulada como auditoría.
- [ ] Restauración visual de una copia SQLite completa.
- [ ] Restauración con vista previa.
- [x] Registrar cambios aceptados, pendientes y rechazados.
- [x] Reintento controlado para JSON inválido/truncado; la respuesta corregida reutiliza el mismo request_id sin duplicar el turno.
- [x] CI: 83 pruebas Python y sintaxis JavaScript aprobadas en modo simulado/manual-input, sin llamadas API pagas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271.
- [x] Continuidad automatizada: 100 turnos breves simulados, reinicialización SQLite, copia, mutación posterior, restauración y comparación exacta del estado/tablas.
- [ ] Campaña narrativa real de 50–100 intercambios con ChatGPT/Gemini web y decisiones variadas.

Criterio de salida: el estado, mensajes y recursos sobreviven al cierre; se pueden detectar y corregir errores de la IA.

## Fase 6 — Segundo proveedor y calidad de vida
- [x] Implementar adaptadores iniciales para OpenAI y Gemini; validación real pendiente.
- [ ] Medición de tokens/coste cuando el proveedor lo exponga.
- [ ] Exportación de mundo, partida y logs.
- [ ] Panel para aprobar cambios pendientes.
- [ ] Importar la Lorebook actual de Isekai sin Destino como banco de prueba.
- [ ] Evaluar memoria semántica, RAG o grafo temporal solo si las pruebas muestran necesidad.

## Estado de los hitos

- **Comprobado por CI:** SQLite, backup, validación Pydantic, normalización del esquema, narrador simulado, turno API de extremo a extremo, reintentos idempotentes, aprobación/rechazo de eventos y creación atómica de mundos con reparto e inventario inicial.
- **No comprobado todavía:** ejecución manual en Windows con chats web reales, compatibilidad de cambios de presencia/datos históricos, restauración visual con vista previa y campaña narrativa de 50–100 turnos con un chat externo. La CI sí comprueba 100 turnos breves simulados y restauración exacta de la base. Las llamadas reales API y sus tokens/costes son una validación opcional distinta.

## Prioridad práctica

La primera entrega útil no necesita personajes animados, imágenes ni un motor 3D. Debe ser aburridamente fiable en los siguientes aspectos: **el texto queda guardado, el estado sobrevive al reinicio, una llamada duplicada no gasta recursos dos veces y una salida de IA no puede cambiar el canon por su cuenta.**


## Creación de mundos

La interfaz ya permite crear un mundo y su primera sesión, con protagonista, canon breve, personajes presentes e inventario inicial. Se crea todo dentro de una transacción; si el reparto tiene nombres duplicados, la operación se revierte. Está cubierto por pruebas automatizadas simuladas; la interfaz aún requiere prueba manual en Windows.

- [x] Validar sintaxis del JavaScript de la interfaz en CI.

Última CI aprobada (83 pruebas Python + JavaScript): https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271


---

## Segunda ronda de prioridades tras investigación y revisión del código

Esta sección distingue implementado de pendiente. No marcar como terminado nada que no haya pasado CI y prueba manual.

### Prioridad P0 — Evitar fugas de conocimiento entre personajes
- [x] Alcance/audiencia por turno: privado con destinatario o escena/grupo, guardado en metadatos.
- [x] Filtrado de contexto por destinatario, audiencia y testigos; eventos pendientes/rechazados no se presentan como hechos confirmados.
- [x] Prueba aislada: conversación privada con Maelis no aparece en el contexto de Ivar; un privado sin destinatario se rechaza.
- [x] Mostrar motivos de inclusión/exclusión de mensajes/eventos con el inspector local: audiencia, destinatario, testigos, estado y límite de historial.
- [x] Migrar tablas antiguas de presencia que carecían de `presence_status`/`updated_at`, normalizar el estado desde la ubicación y restaurar backups sin el campo derivado.
- [x] Mantener mensajes históricos dirigidos limitados al destinatario conservado y excluir eventos sin fuente ni testigos del contexto del modelo.
- [ ] Revisar otras variantes históricas sin metadatos de audiencia aún no cubiertas por pruebas.

**Criterio parcial alcanzado:** privacidad e inspector por mensaje/evento cubiertos por CI; también hay regresiones para destinatarios conservados en mensajes heredados y eventos sin fuente/testigos. Falta revisar otras variantes históricas.

### Prioridad P1 — Política automática para cambios de bajo riesgo
- [x] Mantener revisión para cambios ambiguos y de alto impacto.
- [x] Autoaceptar movimientos de PNJ solo si están presentes en la escena actual, con evento fuente y causa válidos; varios destinos para la misma entidad en un turno quedan pendientes. Se rechaza mover al protagonista sin autorización explícita.
- [x] Validar consumo, condición, soltar/transferir pila completa y recogida de objeto rastreado; requieren objeto/portador/cantidad y evento fuente coherentes.
- [x] Libro de recursos por partida: saldo inicial configurable y monedas a cero en Isekai; ingresos explícitos y compras con coste positivo/moneda/saldo verificados.
- [x] Pago e ingreso/objeto se registran en SQLite con valores anterior/propuesto/aceptado y fuente; saldo insuficiente deja inventario y dinero intactos.
- [x] Mantener objetos de alto impacto, operaciones ambiguas y datos contradictorios pendientes.

**Verificación:** 83 pruebas Python aprobadas en CI (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271),

### Prioridad P2 — Inspector de contexto y activación de Lorebook
- [x] Mostrar fichas Lorebook seleccionadas y los disparadores concretos.
- [x] Usar coincidencia de palabra/frase completa con límites Unicode; se prueba que "corriente Brasa" activa su ficha, pero "brasería" no.
- [x] Limitar Lorebook a 8 entradas y un presupuesto fijo de 4.500 caracteres; los diagnósticos registran entradas omitidas y caracteres empleados.
- [x] Ordenar por pertinencia del mensaje actual/destinatario/lugar/personajes, con prioridad del Lorebook como desempate.
- [x] Presupuesto configurable entre 500–12.000 caracteres desde la UI, persistido en SQLite y usado en turnos/previsualización.
- [x] Mostrar motivo por cada mensaje/evento incluido/excluido.
- [ ] Añadir medición real de tokens por proveedor; el presupuesto aún se expresa en caracteres.

**Criterio parcial alcanzado:** el inspector y el presupuesto editable ya tienen pruebas de CI; falta tokenización exacta por proveedor.

### Prioridad P3 — Undo, editar y regenerar de forma segura
- [x] Crear snapshot preturno con los campos de estado mutables y asociarlo a `turn_id`.
- [x] Anular el último turno completado: restaura reloj, ubicación, presencia, inventario, recursos, relaciones y usos de poderes.
- [x] Conservar auditables las versiones anuladas: mensajes con estado anulada; eventos/cambios rechazados y separados del turno regenerable.
- [x] Permitir reintentar el mismo `request_id` después de undo sin duplicar eventos, compras ni usos de poderes.
- [x] Rechazar el undo de turnos antiguos cuando existan turnos posteriores activos.
 - [ ] Ensayar manualmente la interacción visual en Windows y ampliar escenarios de campaña larga.

**Criterio parcial alcanzado:** restauración de inventario, recursos y reloj, auditoría y orden de undo cubiertos por CI. Quedan escenarios de campaña larga y prueba manual de la interfaz.

### Prioridad P4 — Pruebas de integración reales y de larga duración
- [x] CI Linux: 83 pruebas Python
- [x] CI de compatibilidad de presencia histórica y restauración de backups sin `presence_status`.
- [ ] Ejecutar la instalación desde cero en Windows/Chromium.
- [ ] Probar manualmente en Windows el flujo completo con el chat web normal de ChatGPT y con Gemini.
- [ ] (Opcional para la modalidad API) Probar una llamada controlada a OpenAI API y otra a Gemini API; no almacenar claves en Git.
- [ ] Ejecutar una campaña narrativa de 50–100 turnos con escenas grupales/privadas, compras/consumos, viajes y Eco mediante el flujo real de chat web.
- [x] Comprobación automatizada: reinicializar SQLite tras 100 turnos breves, restaurar la copia tras una mutación y comparar exactamente estado, mensajes y tablas de sesión restaurables.
- [ ] Medir uso del contexto y coste por turno para las APIs cuando el proveedor informe esos datos. En el chat web manual no se promete lectura automática de tokens/coste.

**Criterio de salida:** la partida sobrevive a reinicios y no hay fugas de conocimiento ni efectos duplicados en el conjunto de pruebas.

### Referencias nuevas para la segunda ronda

- Openovel: https://github.com/Feed-Scription/openovel
- Chronicler: https://github.com/yantrikos/chronicler
- RPG Tracker para SillyTavern: https://github.com/Soyo5800/rpg-tracker-for-sillytavern
- Open Dungeon: https://github.com/newideas99/open-dungeon
- Gamentic: https://github.com/hec-ovi/gamentic
- World Info/Lorebook de SillyTavern: https://docs.sillytavern.app/usage/worldinfo/
- Structured Outputs de OpenAI: https://developers.openai.com/api/docs/guides/structured-outputs
- Structured Output de Gemini: https://ai.google.dev/gemini-api/docs/structured-output
- Transacciones SQLite: https://www.sqlite.org/transactional.html


## chat web normal (puente manual)

- [x] Diferenciar explícitamente la suscripción/web chat de las APIs en el selector.
- [x] Preparar desde el estado local un prompt con contexto compacto y contrato JSON.
- [x] Admitir la respuesta pegada de ChatGPT/Gemini y validarla con Pydantic antes de usar el estado propuesto.
- [x] Rechazar respuestas sin JSON válido, sin mutar la partida.
- [x] Rechazar una respuesta pegada si cambió el contexto desde que se preparó el prompt (huella SHA-256).
- [x] Mantener el adaptador API separado y opcional.
- [ ] Hacer la prueba manual en Windows con un chat real de ChatGPT y otro de Gemini.
- [x] Prueba de continuidad sintética de 100 turnos, reinicio, backup, mutación y restauración exacta.
- [ ] Completar una campaña narrativa real de 50–100 turnos y comprobar cierre, reinicio y restauración.

CI aprobada con 83 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271

## Actualización — 29-10-2026, continuidad y restauración

- PR #5 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/5. Commit de integración: `90e8196331406f999ec42f1a4e5b2eb8f4282937`.
- CI: 81 pruebas Python aprobadas y sintaxis JavaScript correcta:
- Añadidos controles de JSON truncado/reintento, compra hipotética, cambios de relación contradictorios y restauración que falla por una restricción de datos. En el fallo de restauración, SQLite revierte la transacción y la API devuelve 422 sin alterar la partida.
- La campaña automatizada de 100 turnos breves ahora compara estado, mensajes y todas las tablas de sesión restaurables antes y después de restaurar una copia tras una mutación posterior.
- Sigue pendiente la prueba manual en Windows y la campaña narrativa de 50–100 turnos con ChatGPT/Gemini web real; la CI usa un proveedor simulado.



## Actualización — 29-10-2026, compatibilidad histórica de presencia (PR #6)

- PR #6 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/6; commit `8a08870b7e3cbba8a107a34a74bd947e919b9c8a`.
- CI posterior a la integración: 81 pruebas Python aprobadas y sintaxis JavaScript correcta (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935903505).
- [x] Actualización in situ de bases cuya tabla `session_presence` carecía de `presence_status` o `updated_at`; los registros se conservan y el estado se recalcula desde la ubicación actual de la partida.
- [x] Restaurar backup histórico cuya tabla de presencia no contiene `presence_status`; el campo derivado se reconstruye al leer la copia.
- [x] Compatibilidad de mensajes dirigidos sin metadatos de audiencia (si el destinatario sigue registrado) y exclusión de eventos sin fuente/testigos del prompt, con diagnóstico.
- [ ] Revisar otras variantes históricas y validarlas manualmente.
- [ ] Prueba manual en Windows/Chromium con ChatGPT web y Gemini web, exportación/restauración visual y campaña de 50–100 turnos reales. Los 100 turnos automatizados siguen siendo breves y usan el proveedor simulado.


## Actualización — 29-10-2026, alcance de audiencia para datos heredados (PR #7)

- PR #7 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/7; commit `63710dd57577481c49a0bbb3bbeb8d232ad42375`.
- CI posterior a la integración: 82 pruebas Python y sintaxis JavaScript correctas (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743).
- [x] Los mensajes antiguos sin `visibility/audience_ids` que conservan `recipient_entity_id` se limitan a ese destinatario.
- [x] Eventos sin mensaje fuente resoluble y sin testigos se excluyen del contexto del modelo; queda diagnóstico y los registros siguen en la base para auditoría.
- [x] La prueba de recuperación de eventos por relevancia usa testigos explícitos; la selección por relevancia no relaja el control de audiencia.
- [ ] Revisar variantes históricas no cubiertas, restauración visual con vista previa, prueba manual Windows/Chromium y campaña narrativa real de 50–100 turnos.


## Actualización — 29-10-2026, privacidad durante undo/regeneración (PR #8)

- PR #8 integrado en `docs/historias-organizadas`: https://github.com/eltiootaku2020-cmyk/wordbot/pull/8; commit `312c10ab4e2cdabc9e92a2842765c7f70fb0b0a5`.
- CI posterior a la integración: **83 pruebas Python aprobadas** y sintaxis JavaScript correcta (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271).
- [x] Prueba combinada de turno privado → undo → regeneración con el mismo `request_id`.
- [x] Verificar que un personaje ajeno no reciba la narración ni el evento confidencial antes del undo, después del undo o después de regenerar.
- [x] Verificar que el destinatario original conserva acceso al diálogo privado regenerado y que el evento anulado queda en auditoría.
- [ ] Prueba manual Windows/Chromium con ChatGPT/Gemini web; restauración visual con vista previa; campaña narrativa real de 50–100 turnos con reinicio/restauración.


## Actualización — 29-10-2026, reintentos con snapshots obsoletos (PR #9 y PR #10)

- [x] Rechazar la regeneración de un turno anulado cuando existe un turno de usuario posterior (PR #9): https://github.com/eltiootaku2020-cmyk/wordbot/pull/9.
- [x] Extender la protección a turnos fallidos y comparar la instantánea preturno con el estado mutable exacto antes de reintentar (PR #10): https://github.com/eltiootaku2020-cmyk/wordbot/pull/10.
- [x] CI PR #10: 86 pruebas Python aprobadas, una advertencia no bloqueante y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940906581.
- [ ] Prueba manual Windows/Chromium con ChatGPT/Gemini web.
- [ ] Campaña narrativa real de 50–100 turnos con checkpoints de backup/restart/restore.
- [ ] Seguir revisando variantes históricas y casos de concurrencia no cubiertos.


## Actualización — 29-10-2026, coherencia de versión del preset (PR #11)

- [x] Etiqueta visible del botón actualizada de v1.16 a v1.19, igual que el Lorebook JSON que el endpoint importa.
- [x] README de la app corregido para v1.19.
- [x] Prueba de regresión: extrae el número de versión de la descripción JSON y lo compara con el número visible en el botón HTML.
- [x] CI: 86 pruebas Python aprobadas y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934304.
- [x] Auditoría de Isekai v1.19: 659 comprobaciones aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934333.
- [ ] Prueba visual manual de Windows/Chromium sigue pendiente.


## Actualización — 29-10-2026, integridad del deshacer (PR #12)

- [x] Detectar si el estado actual difiere del estado posterior al turno que se quiere deshacer usando una huella SHA-256 guardada en el snapshot.
- [x] Rechazar undo con 409 si una aprobación posterior cambió el estado, sin borrar el cambio ni alterar el reloj.
- [x] Preservar el undo de snapshots antiguos cuando no hay una aprobación posterior registrada; bloquear conservadoramente si la hay.
- [x] Mantener compatibilidad con undo/regeneración inmediata y actualizar la huella después de regenerar.
- [x] CI PR #12: 87 pruebas Python y sintaxis JavaScript aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768.
- [ ] Validar manualmente UI Windows/Chromium y campaña real de 50–100 turnos con reinicio/backup/restore.
