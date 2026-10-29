# Roadmap de implementación — gestor local v0.1

El prototipo v0.1 ya existe. Las casillas marcan código presente, no necesariamente validación manual completa. La última CI aprobó 26 pruebas automáticas en Linux/Python 3.12 y comprobó sintaxis JavaScript; proveedores reales y la instalación en Windows aún deben probarse.

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
- [x] Implementar narrador simulado y adaptadores iniciales OpenAI/Gemini; llamadas reales aún no validadas.
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
- [x] Crear copia SQLite consistente; restauración visual y snapshots automáticos siguen pendientes.
- [ ] Restauración con vista previa.
- [x] Registrar cambios aceptados, pendientes y rechazados.
- [ ] Reintento controlado para JSON inválido o timeout.
- [x] CI: 26 pruebas aprobadas en modo simulado, sin llamadas pagas.
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
- **No comprobado todavía:** ejecución en Windows, llamadas reales a OpenAI/Gemini, comportamiento prolongado, reintentos idempotentes y todos los cambios de inventario/movimiento.

## Prioridad práctica

La primera entrega útil no necesita personajes animados, imágenes ni un motor 3D. Debe ser aburridamente fiable en los siguientes aspectos: **el texto queda guardado, el estado sobrevive al reinicio, una llamada duplicada no gasta recursos dos veces y una salida de IA no puede cambiar el canon por su cuenta.**


## Creación de mundos

La interfaz ya permite crear un mundo y su primera sesión, con protagonista, canon breve, personajes presentes e inventario inicial. Se crea todo dentro de una transacción; si el reparto tiene nombres duplicados, la operación se revierte. Está cubierto por pruebas automatizadas simuladas; la interfaz aún requiere prueba manual en Windows.

- [x] Validar sintaxis del JavaScript de la interfaz en CI.

Última CI aprobada (26 pruebas Python + JavaScript): https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40873010055


---

## Segunda ronda de prioridades tras investigación y revisión del código

Esta sección distingue implementado de pendiente. No marcar como terminado nada que no haya pasado CI y prueba manual.

### Prioridad P0 — Evitar fugas de conocimiento entre personajes
- [x] Alcance/audiencia por turno: privado con destinatario o escena/grupo, guardado en metadatos.
- [x] Filtrado de contexto por destinatario, audiencia y testigos; eventos pendientes/rechazados no se presentan como hechos confirmados.
- [x] Prueba aislada: conversación privada con Maelis no aparece en el contexto de Ivar; un privado sin destinatario se rechaza.
- [ ] Mostrar también el motivo por el que cada mensaje/evento se incluyó o excluyó; el inspector ya explica activación de Lorebook y presupuesto.
- [ ] Probar cambios de presencia y registros antiguos sin metadatos de audiencia.

**Criterio parcial alcanzado:** regresión privada cubierta por CI; inspector de mensajes/eventos y pruebas de cambios de escena pendientes.

### Prioridad P1 — Política automática para cambios de bajo riesgo
- [x] Mantener revisión para cambios ambiguos y de alto impacto.
- [x] Autoaceptar movimientos de PNJ con evento fuente registrado, entidad válida, destino y causa; se rechaza mover al protagonista sin autorización explícita.
- [x] Validar consumo, condición, soltar/transferir pila completa y recogida de objeto rastreado; requieren objeto/portador/cantidad y evento fuente coherentes.
- [x] Libro de recursos por partida: saldo inicial configurable y monedas a cero en Isekai; ingresos explícitos y compras con coste positivo/moneda/saldo verificados.
- [x] Pago e ingreso/objeto se registran en SQLite con valores anterior/propuesto/aceptado y fuente; saldo insuficiente deja inventario y dinero intactos.
- [x] Mantener objetos de alto impacto, operaciones ambiguas y datos contradictorios pendientes.

**Verificación:** 26 pruebas Python aprobadas en CI; proveedor simulado. La idempotencia de compra está probada en la API con proveedor simulado; faltan proveedor real y Windows.

### Prioridad P2 — Inspector de contexto y activación de Lorebook
- [x] Mostrar fichas Lorebook seleccionadas y los disparadores concretos.
- [x] Usar coincidencia de palabra/frase completa con límites Unicode; se prueba que "corriente Brasa" activa su ficha, pero "brasería" no.
- [x] Limitar Lorebook a 8 entradas y un presupuesto fijo de 4.500 caracteres; los diagnósticos registran entradas omitidas y caracteres empleados.
- [x] Ordenar por pertinencia del mensaje actual/destinatario/lugar/personajes, con prioridad del Lorebook como desempate.
- [ ] Hacer configurable el presupuesto y mostrar por mensaje/evento la razón de inclusión/exclusión.
- [ ] Añadir medición de tokens real por proveedor; la cifra actual es estimación por caracteres, no tokens.

**Criterio parcial alcanzado:** inspector Lorebook cubierto por prueba de CI. El contexto completo todavía no ofrece un inspector explicativo por mensaje/evento y el límite de caracteres no sustituye un tokenizador.

### Prioridad P3 — Undo, editar y regenerar de forma segura
- [ ] Crear snapshot o conjunto reversible de cambios por turno.
- [ ] Al editar/regenerar, revertir los cambios de ese turno antes de reaplicarlos.
- [ ] Conservar mensajes/respuestas reemplazados en historial de versiones, no borrarlos sin rastro.
- [ ] Asegurar idempotencia para no duplicar gasto de Eco, compra, cambio de relación o avance de reloj.
- [ ] Añadir pruebas de rollback de eventos, inventario, relaciones, tiempo y poderes.

**Criterio de salida:** regenerar una respuesta no duplica ni conserva efectos de la versión que ya no se muestra.

### Prioridad P4 — Pruebas de integración reales y de larga duración
- [x] CI Linux: 26 pruebas Python y comprobación sintáctica de JavaScript aprobadas el 29-10-2026 (no sustituye las pruebas manuales de Windows).
- [ ] Ejecutar la instalación desde cero en Windows/Chromium.
- [ ] Probar una llamada controlada a OpenAI y otra a Gemini con claves del usuario en su PC; no almacenar claves en Git.
- [ ] Ejecutar 50–100 turnos con escenas grupales/privadas, compras/consumos, viajes y Eco.
- [ ] Reiniciar la aplicación, restaurar backup y verificar que el estado sea idéntico.
- [ ] Medir uso del contexto y coste por turno en cada proveedor cuando los datos estén disponibles.

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
