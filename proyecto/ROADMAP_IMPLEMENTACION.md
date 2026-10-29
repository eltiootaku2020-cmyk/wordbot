# Roadmap de implementación — gestor local v0.1

El proyecto está en fase de investigación y especificación. Las fases siguientes son propuestas de trabajo, no funcionalidades terminadas.

## Fase 0 — Investigación y arquitectura
- [x] Revisar clientes de roleplay (SillyTavern, RisuAI, Agnai).
- [x] Revisar memoria persistente (LangGraph, Mem0, Graphiti).
- [x] Revisar Structured Outputs de OpenAI y salida estructurada de Gemini.
- [x] Revisar transacciones, WAL y copias de seguridad de SQLite.
- [x] Documentar restricciones de la página de consumo y facturación API.
- [x] Preparar las decisiones técnicas provisionales.
- [ ] Revisar la decisión con una prueba técnica pequeña.

## Fase 1 — Esqueleto ejecutable
- [ ] Crear estructura del paquete Python y configuración de entorno.
- [ ] Crear SQLite y migraciones iniciales.
- [ ] Crear endpoints locales para mundos, partidas, mensajes y estado.
- [ ] Crear página de chat mínima abierta en Chromium.
- [ ] Crear configuración de proveedor y manejo seguro de claves.
- [ ] Añadir pantalla de error y log local.

Criterio de salida: se puede crear/seleccionar un mundo, enviar un mensaje simulado, guardar texto y reiniciar sin perderlo; aún no requiere un proveedor real.

## Fase 2 — Un turno completo con salida estructurada
- [ ] Implementar un adaptador de proveedor inicial.
- [ ] Enviar contexto reducido.
- [ ] Recibir narración + eventos + cambios propuestos conforme al esquema.
- [ ] Validar estructura e IDs.
- [ ] Guardar narración, propuestas y resultado de validación.
- [ ] Implementar idempotencia para que un reintento no duplique operaciones.

Criterio de salida: el caso «Hola, linda» genera una escena y un registro del intercambio, sin requerir un bloque de guardado en el chat.

## Fase 3 — Estado esencial del juego
- [ ] Reloj, día, bloque, ubicación y personajes presentes.
- [ ] Inventario con cantidad, condición, portador y ubicación.
- [ ] Relaciones por eje, con causa y fuente.
- [ ] Habilidades/recursos y usos limitados de poderes.
- [ ] Registro de eventos y procedencia del conocimiento de cada PNJ.
- [ ] Validaciones de acciones, movimiento, compras y usos de habilidades.

Criterio de salida: un cambio sólo se aplica si tiene una causa válida; el mismo mensaje no puede descontar un poder dos veces.

## Fase 4 — Lorebook y recuperación
- [ ] Importar/exportar entradas Markdown/JSON.
- [ ] Activar fichas por personajes presentes, palabras clave y contexto de la escena.
- [ ] Resolver conflictos de prioridades y estados canon/pendiente/rumor.
- [ ] Añadir búsqueda de eventos/diálogos antiguos.
- [ ] Definir un presupuesto de tokens configurable y mostrar qué se envió al modelo.

Criterio de salida: el programa envía solo el lore necesario y no convierte un rumor en hecho.

## Fase 5 — Fiabilidad y recuperación
- [ ] Snapshots y backup SQLite consistentes.
- [ ] Restauración con vista previa.
- [ ] Registro de cambios aceptados/rechazados.
- [ ] Reintento controlado para JSON inválido o timeout.
- [ ] Pruebas automatizadas sin llamadas pagas.
- [ ] Prueba de 50–100 intercambios y reinicio completo.

Criterio de salida: el estado, mensajes y recursos sobreviven al cierre; se pueden detectar y corregir errores de la IA.

## Fase 6 — Segundo proveedor y calidad de vida
- [ ] Adaptador del segundo proveedor (OpenAI/Gemini en orden configurable).
- [ ] Medición de tokens/coste cuando el proveedor lo exponga.
- [ ] Exportación de mundo, partida y logs.
- [ ] Panel para aprobar cambios pendientes.
- [ ] Importar la Lorebook actual de Isekai sin Destino como banco de prueba.
- [ ] Evaluar memoria semántica, RAG o grafo temporal solo si las pruebas muestran necesidad.

## Prioridad práctica

La primera entrega útil no necesita personajes animados, imágenes ni un motor 3D. Debe ser aburridamente fiable en los siguientes aspectos: **el texto queda guardado, el estado sobrevive al reinicio, una llamada duplicada no gasta recursos dos veces y una salida de IA no puede cambiar el canon por su cuenta.**
