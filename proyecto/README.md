# Proyecto: gestor local de canon, Lorebooks y continuidad

**Estado:** prototipo de desarrollo v0.1. Código inicial disponible; CI: 12 pruebas aprobadas el 29-10-2026. Falta instalación/uso real en el PC y validación de APIs con credenciales.  
**Ubicación de trabajo:** rama `docs/historias-organizadas`, carpeta `proyecto/`.

## Objetivo

Crear una aplicación para PC que conserve los mundos, Lorebooks, personajes, cronología, conversaciones e historial de cambios de una partida. La IA se ocupa de interpretar la escena y redactar la siguiente respuesta; la aplicación local administra el canon y el estado persistente.

La regla central es:

> **La IA narra y propone. El programa valida, guarda y mantiene el estado oficial de la partida.**

No se debe enviar el Lorebook entero en cada mensaje. La aplicación recupera solo las reglas, fichas, hechos y mensajes relevantes para la escena actual.

## Flujo de un turno

1. El usuario escribe un mensaje y, si hace falta, selecciona el destinatario.
2. La aplicación recupera el estado actual y un contexto reducido: lugar, hora, personajes presentes, sus fichas, relaciones relevantes, reglas activas y últimos intercambios.
3. El conector envía ese contexto y el mensaje a la IA.
4. La IA devuelve la narración para mostrar al usuario, los acontecimientos que afirma que sucedieron y una lista separada de cambios propuestos.
5. Un validador local comprueba el formato, los permisos narrativos y las reglas del mundo.
6. Los cambios válidos se aplican en una transacción de SQLite y quedan en el registro de eventos. Los ambiguos o de alto impacto pueden quedar pendientes de aprobación.
7. La aplicación muestra la narración en el chat y, opcionalmente, un indicador discreto de «Guardado». No inserta un bloque largo de estadísticas en la conversación.

## Principios de diseño

- **Canon separado por mundo:** Isekai sin Destino, DanMachi y futuros mundos no comparten personajes, reglas ni estado.
- **Contexto selectivo:** recuperar por escena, ubicación, personajes, palabras clave y hechos pendientes; nunca volcar toda la biblioteca por defecto.
- **Fuente de verdad local:** SQLite conserva el estado aceptado aunque se cierre el programa o el modelo olvide intercambios anteriores.
- **Historial auditable:** cada cambio guarda su causa, fuente, fecha de partida, entidad afectada y valores anteriores/nuevos.
- **Hecho no es rumor:** diferenciar canon, hecho confirmado, observación, rumor, hipótesis y propuesta de la IA.
- **Agencia del usuario:** la IA no decide las palabras, acciones, decisiones ni pensamientos del protagonista.
- **Cambios verificables:** una afirmación de la IA no se convierte automáticamente en canon solo porque aparezca en una respuesta.
- **Sin memoria ficticia:** si falta información, se marca como desconocida o se pregunta; no se inventa para completar un formulario.
- **Privacidad local:** Lorebook, registros e inventario se almacenan en el PC. Solo se envía al proveedor el contexto necesario para generar la respuesta.
- **Sin extracción de páginas web:** priorizar conectores oficiales por API en lugar de depender de leer o controlar automáticamente las páginas web de chat.

## Investigación, decisiones y plan de implementación

- [Investigación de proyectos y referencias](INVESTIGACION_REFERENCIAS.md)
- [Decisiones técnicas provisionales](DECISIONES_TECNICAS.md)
- [Roadmap de implementación](ROADMAP_IMPLEMENTACION.md)

La investigación recomienda una interfaz web local en Chromium, backend Python/FastAPI, SQLite y adaptadores para APIs oficiales. No se leerá automáticamente la pestaña de ChatGPT de consumo. La decisión podrá reconsiderarse tras una prueba técnica de un solo turno.

## Código del prototipo

- [Guía de ejecución](app/README.md)
- [Fuente principal y API local](app/src/canon_manager/main.py)
- [Interfaz de chat para Chromium](app/src/canon_manager/static/index.html)
- [Base de datos y esquema SQLite](app/src/canon_manager/db.py)
- [Narrador simulado y adaptadores OpenAI/Gemini](app/src/canon_manager/providers.py)
- [Pruebas automáticas](app/tests/)
- [Ejecución CI: 12 pruebas aprobadas](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40863082953)

La prueba de integración ejecuta el flujo «Hola, linda» dirigido a Maelis: guarda mensajes, registra reacciones, deja pendiente el cambio numérico si no existe una base confirmada y conserva hora e inventario. También se prueba crear un mundo personalizado con protagonista, reparto e inventario inicial, y comprobar que si falla por nombres duplicados se revierte toda la operación. Esto valida el modo simulado; no sustituye la prueba manual en Windows ni las llamadas reales a proveedores.

## Componentes previstos

- Interfaz local de chat y panel de estado.
- Selector de mundo, partida, personaje destinatario y proveedor de IA.
- Gestor de Lorebooks con activación selectiva.
- Constructor de contexto compacto.
- Adaptador de modelo intercambiable.
- Contrato estructurado de respuesta IA: [CONTRATO_RESPUESTA_IA.md](CONTRATO_RESPUESTA_IA.md).
- Validador de reglas y motor de aplicación de cambios.
- Base de datos local y registro de eventos: [ESQUEMA_LOCAL.md](ESQUEMA_LOCAL.md).
- Copias de seguridad, exportación y restauración.
- Pruebas: [PRUEBAS_DE_ACEPTACION.md](PRUEBAS_DE_ACEPTACION.md).

## Tecnología provisional elegida

- Python + FastAPI para backend local.
- HTML/CSS/JavaScript ligero para la interfaz en Chromium.
- SQLite con transacciones y WAL para persistencia local.
- Proveedor simulado sin coste, más adaptadores iniciales para APIs oficiales de OpenAI y Gemini.
- Importación de Lorebook JSON compatible con SpicyChat y recuperación de entradas por palabras clave.

La decisión se basa en la investigación enlazada y puede revisarse después de probar el prototipo en Windows. El uso de API puede facturarse por separado de una suscripción de chat.

## Alcance del primer prototipo

1. Crear/seleccionar mundo y partida.
2. Importar fichas y Lorebook desde JSON/Markdown.
3. Registrar y mostrar una conversación.
4. Consultar solo contexto relevante para cada turno.
5. Recibir una respuesta estructurada de la IA.
6. Validar y guardar mensajes, acontecimientos y cambios aceptados en SQLite.
7. Consultar inventario, reloj, lugar, relaciones y usos de habilidades.
8. Cerrar y reabrir la aplicación sin perder el estado.
9. Exportar un guardado y restaurarlo.
10. Mostrar cambios rechazados o pendientes sin aplicarlos silenciosamente.

## Fuera del alcance inicial

- Entrenar un modelo propio.
- Ejecutar un modelo grande localmente.
- Compatibilidad automática con cualquier página de chat del navegador.
- Cambiar el canon del mundo sin autorización.
- Simular un motor de combate complejo antes de validar la continuidad básica.

## Estado y siguientes pasos

**Estado actual:** el prototipo tiene interfaz y backend, guarda mensajes y estado en SQLite, ofrece un narrador simulado y permite importar una Lorebook JSON. Las 8 pruebas de CI pasan. Pendiente: prueba manual en Windows, llamadas API reales, idempotencia de reintentos, aprobación de eventos importantes, validación completa de movimientos e inventario, exportación/restauración visual y prueba de 50–100 intercambios.
