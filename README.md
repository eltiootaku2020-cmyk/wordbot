# Proyectos de bots de SpicyChat y herramientas de continuidad

Este repositorio organiza mundos, bots e historias con sus propias carpetas, configuración, Lorebooks y registros. No mezclar el canon ni el estado de proyectos diferentes.

## Herramienta en desarrollo

- [Gestor local de canon, Lorebooks y continuidad](proyecto/README.md) — prototipo v0.1 con código en [proyecto/app](proyecto/app/README.md). La CI del PR #14 aprobó **89 pruebas Python y la comprobación de sintaxis JavaScript** ([ejecución](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40946590907)); queda una advertencia no bloqueante de Starlette/httpx. La auditoría del Lorebook Isekai v1.19 pasó 659 comprobaciones ([auditoría](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934333)). Incluye 77 entradas, creación de mundos, validación de acciones, reintentos idempotentes, restauración tras 100 turnos breves simulados, filtros conservadores de audiencia y controles de deshacer/reintentar. PR #13 bloquea aprobaciones durante generación; PR #14 añade recuperación al cancelar una generación sin duplicar turnos. Faltan prueba manual en Windows/Chromium y campaña de 50–100 turnos con ChatGPT/Gemini web reales. PR #14 sigue pendiente de integración en `docs/historias-organizadas`; `main` permanece intacta. Incluye [investigación](proyecto/INVESTIGACION_REFERENCIAS.md), [comparativa de programas similares y errores fantasma](proyecto/INVESTIGACION_PROGRAMAS_SIMILARES_Y_ERRORES_FANTASMA_2026-10-29.md), [decisiones](proyecto/DECISIONES_TECNICAS.md), [roadmap](proyecto/ROADMAP_IMPLEMENTACION.md) y [arquitectura](proyecto/ARQUITECTURA.md).

## Historias

- [Isekai sin Destino](proyectos/isekai-sin-destino/README.md) — fantasía abierta, supervivencia, Eco, cronología regional y continuidad de partida.
- [DanMachi](proyectos/danmachi/README.md) — aventura en Orario, Familias, Falna y Dungeon; varias decisiones iniciales siguen pendientes.

## Regla de organización

La rama `docs/historias-organizadas` es la vista organizada de trabajo: aquí están las carpetas de los mundos y las Lorebooks, y aquí deben añadirse los cambios para mantener una única versión organizada. La rama literal `main` aún no contiene estas carpetas (solo conserva `.gitignore`); no se ha sincronizado ni reemplazado en esta tarea.
