# Proyectos de bots de SpicyChat y herramientas de continuidad

Este repositorio organiza mundos, bots e historias con sus propias carpetas, configuración, Lorebooks y registros. No mezclar el canon ni el estado de proyectos diferentes.

## Herramienta en desarrollo

- [Gestor local de canon, Lorebooks y continuidad](proyecto/README.md) — prototipo v0.1 con código en [proyecto/app](proyecto/app/README.md). CI: 12 pruebas aprobadas; ya incluye creación de mundos personalizados, reintentos idempotentes y revisión de eventos. Falta validación manual en Windows y pruebas de proveedores reales. Incluye [investigación](proyecto/INVESTIGACION_REFERENCIAS.md), [decisiones](proyecto/DECISIONES_TECNICAS.md), [roadmap](proyecto/ROADMAP_IMPLEMENTACION.md) y [arquitectura](proyecto/ARQUITECTURA.md).

## Historias

- [Isekai sin Destino](proyectos/isekai-sin-destino/README.md) — fantasía abierta, supervivencia, Eco, cronología regional y continuidad de partida.
- [DanMachi](proyectos/danmachi/README.md) — aventura en Orario, Familias, Falna y Dungeon; varias decisiones iniciales siguen pendientes.

## Regla de organización

La rama `docs/historias-organizadas` es la vista organizada de trabajo: aquí están las carpetas de los mundos y las Lorebooks, y aquí deben añadirse los cambios para mantener una única versión organizada. La rama literal `main` aún no contiene estas carpetas (solo conserva `.gitignore`); no se ha sincronizado ni reemplazado en esta tarea.
