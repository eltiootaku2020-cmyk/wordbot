# Proyecto: gestor local de canon, Lorebooks y continuidad

**Estado:** prototipo local v0.1. CI posterior al PR #7 aprobó 82 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743. Además de continuidad y migración de presencia/backup, cubre mensajes heredados limitados a su destinatario y eventos sin fuente/testigos excluidos del prompt. Falta ensayo manual en Windows, restauración visual y campaña narrativa larga con chat externo; las pruebas reales de API son opcionales.
**Ubicación de trabajo:** rama `docs/historias-organizadas`, carpeta `proyecto/`.

## Objetivo

Crear una aplicación para PC que conserve los mundos, Lorebooks, personajes, cronología, conversaciones e historial de cambios de una partida. La IA se ocupa de interpretar la escena y redactar la siguiente respuesta; la aplicación local administra el canon y el estado persistente.

La regla central es:

> **La IA narra y propone. El programa valida, guarda y mantiene el estado oficial de la partida.**

No se debe enviar el Lorebook entero en cada mensaje. La aplicación recupera solo las reglas, fichas, hechos y mensajes relevantes para la escena actual.

## Flujo de un turno

1. El usuario escribe un mensaje y, si hace falta, selecciona el destinatario.
2. La aplicación recupera el estado actual y un contexto reducido: lugar, hora, personajes presentes, sus fichas, relaciones relevantes, reglas activas y últimos intercambios.
3. Según el modo elegido: en el modo manual, la aplicación prepara un prompt que tú copias al chat web normal de ChatGPT o Gemini; en el modo API opcional, el adaptador oficial envía la solicitud.
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
- **Chat web manual como vía de uso:** puedes copiar el prompt a tu conversación normal y pegar de vuelta la respuesta. La aplicación no automatiza el inicio de sesión ni lee la página; los adaptadores API son una modalidad separada y optativa.

## Investigación, decisiones y plan de implementación

- [Investigación de proyectos y referencias](INVESTIGACION_REFERENCIAS.md) — incluye Openovel, Chronicler, RPG Tracker, Open Dungeon, Gamentic, SillyTavern, RisuAI, memoria y APIs.
- [Decisiones técnicas provisionales](DECISIONES_TECNICAS.md) — ADR-001 a ADR-015.
- [Roadmap de implementación](ROADMAP_IMPLEMENTACION.md) — prioridades P0–P4 y pruebas pendientes.

Para el uso previsto, la interfaz local en Chromium + FastAPI + SQLite incluye un puente manual de copia/pega para el chat web normal. Las API oficiales siguen disponibles como modalidad separada y optativa. No se leerá automáticamente la pestaña de ChatGPT/Gemini.

## Código del prototipo

- [Guía de ejecución](app/README.md)
- [Fuente principal y API local](app/src/canon_manager/main.py)
- [Interfaz de chat para Chromium](app/src/canon_manager/static/index.html)
- [Base de datos y esquema SQLite](app/src/canon_manager/db.py)
- [Narrador simulado y adaptadores OpenAI/Gemini](app/src/canon_manager/providers.py)
- [Pruebas automáticas](app/tests/)
- [Ejecución CI más reciente: 82 pruebas aprobadas](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743)

Las pruebas de integración cubren «Hola, linda» con Maelis, eventos y cambios pendientes, creación atómica de mundos, el preset de Isekai (77 entradas), privacidad por audiencia, presupuesto Lorebook, undo/recursos y el puente manual ChatGPT/Gemini. La CI valida el modo simulado, la preparación del prompt y el JSON pegado; no sustituye la prueba manual en Windows. Las llamadas API reales son opcionales.

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

**Estado actual:** el código incluye interfaz Chromium, SQLite, narrador simulado, adaptadores API opcionales y modo manual para chat web normal de ChatGPT/Gemini. CI aprueba 82 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743); cubre JSON truncado, acciones hipotéticas, propuestas contradictorias, restauración tras 100 turnos simulados, migración de presencia y reglas conservadoras de audiencia histórica. Los eventos sin fuente ni testigos se conservan para auditoría pero no se envían al modelo. Falta validación visual manual en Windows y campaña narrativa con chat externo real.

**Prioridades actuales:** probar el puente manual con ChatGPT web y Gemini web en Windows; revisar variantes históricas aún no representadas por las pruebas; completar restauración visual con vista previa y realizar una campaña narrativa real de 50–100 turnos. La medición de coste de las APIs queda como validación opcional.


### Corrección del modo de IA: chat web normal

El usuario puede elegir ahora **ChatGPT web** o **Gemini web** y continuar en el chat normal de su cuenta, sin clave API. La aplicación prepara el prompt con el estado local y el esquema JSON; el usuario copia el prompt al sitio oficial y después pega la respuesta para que el programa la valide y aplique sus reglas. No se automatiza ni se lee la sesión de navegador.

Implementado en `docs/historias-organizadas`; CI actual de 82 pruebas Python y sintaxis JS: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743. La huella SHA-256 impide aplicar una respuesta si el contexto cambió desde la preparación. Pendiente prueba manual real en Windows con ambos chats, restauración visual y campaña narrativa de 50–100 turnos.
