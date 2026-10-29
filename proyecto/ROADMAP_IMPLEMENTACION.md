# Roadmap de implementación — gestor local v0.1

El prototipo v0.1 ya existe. Las casillas marcan código presente, no necesariamente validación manual completa. La CI aprobó 13 pruebas automáticas en Linux/Python 3.12; proveedores reales y la instalación en Windows aún deben probarse.

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
- [x] Enviar contexto reducido con estado, participantes, historial reciente y Lorebook relevante (máximo 12 entradas).
- [x] Recibir narración, eventos y cambios propuestos en un contrato Pydantic/JSON.
- [x] Validar estructura, entidades y evento fuente; la validación semántica completa sigue pendiente.
- [x] Guardar mensajes, eventos y cambios aceptados/pendientes/rechazados en SQLite.
- [x] Implementar clave de idempotencia a nivel de solicitud y reutilizar la respuesta guardada en un reintento.

Criterio de salida: el caso «Hola, linda» genera una escena y un registro del intercambio, sin requerir un bloque de guardado en el chat.

## Fase 3 — Estado esencial del juego
- [x] Guardar día, hora, ubicación y personajes presentes; reloj básico y /salto explícito implementados.
- [x] Guardar inventario con cantidad, condición, portador y ubicación; operaciones nuevas requieren aprobación.
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
- [x] CI: 8 pruebas aprobadas en modo simulado, sin llamadas pagas.
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

Última CI aprobada (13 pruebas Python + JavaScript): https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40863341616


---

## Segunda ronda de prioridades tras investigación y revisión del código

Esta sección distingue implementado de pendiente. No marcar como terminado nada que no haya pasado CI y prueba manual.

### Prioridad P0 — Evitar fugas de conocimiento entre personajes
- [ ] Añadir alcance/audiencia a mensajes: privado, destinatario, grupo o público.
- [ ] Filtrar contexto reciente por destinatario, testigos y transmisión de información.
- [ ] Añadir pruebas: una conversación privada con Maelis no aparece al hablar después con Ivar; Ivar solo lo sabe si alguien se lo cuenta y queda registrado.
- [ ] Mostrar en el inspector la razón por la que cada recuerdo es visible al PNJ.

**Criterio de salida:** ningún secreto se envía a un narrador de PNJ sin una fuente de conocimiento válida.

### Prioridad P1 — Política automática para cambios de bajo riesgo
- [ ] Mantener revisión para cambios ambiguos y de alto impacto.
- [ ] Implementar autoaceptación de movimientos cotidianos de PNJ solo con evento fuente válido, entidad registrada, destino plausible y causa.
- [ ] Implementar operaciones de inventario normal (compra, consumo, soltar, entregar) con objeto, cantidad, saldo/coste cuando corresponda y evento fuente verificables.
- [ ] Exigir aprobación para objetos únicos/mágicos, muertes, giros de canon, nuevos poderes y decisiones del protagonista no explícitas.
- [ ] Registrar valor anterior/propuesto/aceptado, motivo y fuente.

**Criterio de salida:** un intercambio cotidiano se guarda automáticamente; una propuesta incierta no cambia el estado oficial silenciosamente.

### Prioridad P2 — Inspector de contexto y activación de Lorebook
- [ ] Mostrar las fichas activadas y su disparador.
- [ ] Sustituir búsquedas accidentales por subcadena por un modo de coincidencia configurable (frase/palabra completa/regex limitada).
- [ ] Añadir presupuesto de contexto por tokens aproximados o caracteres, además del máximo de entradas.
- [ ] Ordenar por prioridad y pertinencia de entidades/escena.
- [ ] Probar que una ficha con una palabra corta (por ejemplo un nombre de corriente mágica) no se active en texto ajeno por accidente.

**Criterio de salida:** el usuario puede inspeccionar el contexto enviado y entender por qué entró o no entró una ficha.

### Prioridad P3 — Undo, editar y regenerar de forma segura
- [ ] Crear snapshot o conjunto reversible de cambios por turno.
- [ ] Al editar/regenerar, revertir los cambios de ese turno antes de reaplicarlos.
- [ ] Conservar mensajes/respuestas reemplazados en historial de versiones, no borrarlos sin rastro.
- [ ] Asegurar idempotencia para no duplicar gasto de Eco, compra, cambio de relación o avance de reloj.
- [ ] Añadir pruebas de rollback de eventos, inventario, relaciones, tiempo y poderes.

**Criterio de salida:** regenerar una respuesta no duplica ni conserva efectos de la versión que ya no se muestra.

### Prioridad P4 — Pruebas de integración reales y de larga duración
- [ ] Ejecutar la instalación desde cero en Windows/Chromium.
- [ ] Probar una llamada controlada a OpenAI y otra a Gemini usando claves del usuario en su PC; no almacenar claves en Git.
- [ ] Ejecutar 50–100 turnos con conversación grupal, mensajes privados, compras/consumos, viajes y Eco.
- [ ] Reiniciar aplicación, restaurar backup y verificar que el estado sea idéntico.
- [ ] Medir uso del contexto y coste por turno en cada proveedor cuando esos datos estén disponibles.

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
