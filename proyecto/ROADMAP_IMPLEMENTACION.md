# Roadmap de implementación — gestor local v0.1

El prototipo v0.1 ya existe. Las casillas marcan código presente, no necesariamente validación manual completa. La CI del 29-10-2026 aprobó 35 pruebas automáticas en Linux/Python 3.12 y comprobó sintaxis JavaScript. Ya existe un puente manual para el chat web normal de ChatGPT/Gemini; la interfaz e intercambio real deben probarse en Windows. Las APIs son opcionales.

## Fase 0 — Investigación y arquitectura
- [x] Revisar clientes de roleplay (SillyTavern, RisuAI, Agnai).
- [x] Revisar memoria persistente (LangGraph, Mem0, Graphiti).
- [x] Revisar Structured Outputs de OpenAI y salida estructurada de Gemini.
- [x] Revisar transacciones, WAL y copias de seguridad de SQLite.
- [x] Documentar restricciones de la página de consumo y facturación API.
- [x] Preparar las decisiones técnicas provisionales.
- [x] Crear y probar un flujo pequeño con proveedor simulado.
- [x] Cargar preset de Isekai sin Destino y validar las 76 entradas, reparto, inventario inicial y nueva sesión.
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
- [ ] Validaciones de acciones, movimiento, compras y usos de habilidades.

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
- [ ] Reintento controlado para JSON inválido o timeout.
- [x] CI: 35 pruebas Python y sintaxis JavaScript aprobadas en modo simulado/manual-input, sin llamadas API pagas.
- [ ] Prueba de 50–100 intercambios y reinicio completo.

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
- **No comprobado todavía:** ejecución manual en Windows con chats web reales, compatibilidad de cambios de presencia/datos históricos, campaña de 50–100 turnos y restauración visual del backup. Las llamadas reales API y sus tokens/costes son una validación opcional distinta.

## Prioridad práctica

La primera entrega útil no necesita personajes animados, imágenes ni un motor 3D. Debe ser aburridamente fiable en los siguientes aspectos: **el texto queda guardado, el estado sobrevive al reinicio, una llamada duplicada no gasta recursos dos veces y una salida de IA no puede cambiar el canon por su cuenta.**


## Creación de mundos

La interfaz ya permite crear un mundo y su primera sesión, con protagonista, canon breve, personajes presentes e inventario inicial. Se crea todo dentro de una transacción; si el reparto tiene nombres duplicados, la operación se revierte. Está cubierto por pruebas automatizadas simuladas; la interfaz aún requiere prueba manual en Windows.

- [x] Validar sintaxis del JavaScript de la interfaz en CI.

Última CI aprobada (35 pruebas Python + JavaScript): https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40880074124


---

## Segunda ronda de prioridades tras investigación y revisión del código

Esta sección distingue implementado de pendiente. No marcar como terminado nada que no haya pasado CI y prueba manual.

### Prioridad P0 — Evitar fugas de conocimiento entre personajes
- [x] Alcance/audiencia por turno: privado con destinatario o escena/grupo, guardado en metadatos.
- [x] Filtrado de contexto por destinatario, audiencia y testigos; eventos pendientes/rechazados no se presentan como hechos confirmados.
- [x] Prueba aislada: conversación privada con Maelis no aparece en el contexto de Ivar; un privado sin destinatario se rechaza.
- [x] Mostrar motivos de inclusión/exclusión de mensajes/eventos con el inspector local: audiencia, destinatario, testigos, estado y límite de historial.
- [ ] Probar cambios de presencia y registros antiguos sin metadatos de audiencia.

**Criterio parcial alcanzado:** privacidad e inspector por mensaje/evento cubiertos por CI; quedan cambios de presencia y registros históricos sin metadatos.

### Prioridad P1 — Política automática para cambios de bajo riesgo
- [x] Mantener revisión para cambios ambiguos y de alto impacto.
- [x] Autoaceptar movimientos de PNJ con evento fuente registrado, entidad válida, destino y causa; se rechaza mover al protagonista sin autorización explícita.
- [x] Validar consumo, condición, soltar/transferir pila completa y recogida de objeto rastreado; requieren objeto/portador/cantidad y evento fuente coherentes.
- [x] Libro de recursos por partida: saldo inicial configurable y monedas a cero en Isekai; ingresos explícitos y compras con coste positivo/moneda/saldo verificados.
- [x] Pago e ingreso/objeto se registran en SQLite con valores anterior/propuesto/aceptado y fuente; saldo insuficiente deja inventario y dinero intactos.
- [x] Mantener objetos de alto impacto, operaciones ambiguas y datos contradictorios pendientes.

**Verificación:** 35 pruebas Python aprobadas en CI, incluidos los tests del puente manual. La idempotencia de compra está probada con proveedor simulado; falta Windows y uso manual real de ChatGPT/Gemini.

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
- [x] CI Linux: 35 pruebas Python y comprobación sintáctica de JavaScript aprobadas el 29-10-2026 (no sustituye las pruebas manuales de Windows).
- [ ] Ejecutar la instalación desde cero en Windows/Chromium.
- [ ] Probar manualmente en Windows el flujo completo con el chat web normal de ChatGPT y con Gemini.
- [ ] (Opcional para la modalidad API) Probar una llamada controlada a OpenAI API y otra a Gemini API; no almacenar claves en Git.
- [ ] Ejecutar 50–100 turnos con escenas grupales/privadas, compras/consumos, viajes y Eco.
- [ ] Reiniciar la aplicación, restaurar backup y verificar que el estado sea idéntico.
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
- [x] Mantener el adaptador API separado y opcional.
- [ ] Hacer la prueba manual en Windows con un chat real de ChatGPT y otro de Gemini.
- [ ] Completar la campaña de 50–100 turnos y comprobar cierre, reinicio y restauración.

**Criterio para la primera entrega sin API:** el usuario puede usar su cuenta normal en el sitio web mediante copiar/pegar; el programa conserva y valida el estado localmente. No se requiere que las APIs estén configuradas ni se automatiza la lectura del chat web. CI de este modo aprobada: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40880074124.
