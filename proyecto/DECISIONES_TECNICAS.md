# Decisiones técnicas — gestor local v0.1

Estado: decisiones provisionales informadas por la investigación. No equivalen a código implementado.

## ADR-001 — La base local es la fuente de verdad

**Decisión:** SQLite conserva todo estado confirmado. La IA no puede escribir directamente en la base. Devuelve un contrato estructurado; el validador local decide qué operaciones se aplican.

**Motivo:** una salida de IA puede ser sintácticamente válida pero narrativamente incorrecta. El estado oficial necesita integridad, historial y reversión.

## ADR-002 — Cliente web local, no extracción del chat de consumo

**Decisión:** el primer prototipo tendrá una interfaz ligera abierta en Chromium en una dirección de loopback local, por ejemplo `http://127.0.0.1:8000`. No automatizará la lectura o extracción de respuestas desde la pestaña de ChatGPT de consumo.

**Motivo:** las condiciones de OpenAI para ChatGPT de consumo prohíben extracción programática de datos o respuestas; la API es una vía distinta. Véase [investigación y fuentes](INVESTIGACION_REFERENCIAS.md).

**Alternativa evaluable:** una extensión local para SillyTavern, que ya ofrece chat de rol, lorebooks y proveedores, si la construcción de una interfaz propia se vuelve el mayor obstáculo. Debe evaluarse la licencia AGPL-3.0 y la compatibilidad de la extensión antes de distribuirla.

## ADR-003 — Stack del primer prototipo

- Backend: Python + FastAPI.
- Frontend: HTML/CSS/JavaScript ligero; sin un framework grande en la primera versión.
- Persistencia: SQLite.
- Validación: modelos de datos de Python con tipos estrictos; contrato JSON Schema compartido con el proveedor.
- IA: adaptadores intercambiables para las APIs oficiales de OpenAI y Gemini.
- Distribución inicial: ejecutar localmente y abrir la URL en Chromium; empaquetado de escritorio solo después de validar el flujo.

**Motivo:** mantiene el uso de memoria local bajo, permite usar modelos remotos y deja el navegador como interfaz sin extraer datos de páginas ajenas. No requiere una GPU potente para inferencia local porque no ejecuta el modelo en la PC.

## ADR-004 — Contexto selectivo en lugar de Lorebook completa

Cada turno carga:
1. reglas fundamentales;
2. estado actual;
3. fichas de entidades presentes o aludidas;
4. Lorebook activada por nombre/palabra clave;
5. mensajes/eventos recientes y recuerdos recuperados por relevancia;
6. reglas específicas de la acción (inventario, viaje, magia, Eco).

La selección tiene presupuesto de tokens configurable. Nunca se envía la base de datos completa por defecto.

## ADR-005 — Estado tabular + registro de eventos, sin grafo obligatorio

**Decisión:** empezar con tablas SQLite para mundos, partidas, entidades, Lorebook, mensajes, eventos, cambios de estado, inventario, relaciones, usos de habilidades y snapshots.

Cada cambio conserva causa, fuente, estado de validación y valores anterior/propuesto/aceptado. Los mensajes son el archivo completo; el resumen actual no sustituye al historial.

**No incluir en v0.1:** Graphiti, Mem0, embeddings ni vector DB como dependencia obligatoria. Se pueden evaluar más adelante para recuperar recuerdos narrativos antiguos, pero no deben decidir cantidades o reglas de canon.

## ADR-006 — Salida estructurada más validación semántica

El proveedor debe producir la narración y los cambios en campos separados. Se usará el subconjunto común de JSON Schema compatible con ambos proveedores. Después:
- validar estructura y tipos;
- validar IDs y reglas de mundo;
- asociar cambios a eventos;
- rechazar claves/operaciones desconocidas;
- pedir aprobación para cambios irreversibles o ambiguos;
- aplicar cambios válidos en una transacción;
- almacenar un ID idempotente generado por el programa para no repetir cambios al reintentar.

## ADR-007 — Historial recuperable y backups

- Guardar mensajes originales y narración final.
- Guardar cada acontecimiento y cambio aceptado/rechazado/pendiente.
- Crear snapshots automáticos y copias de seguridad exportables.
- Usar transacciones SQLite y mecanismo de backup consistente con WAL.
- Permitir restaurar una partida sin cambiar el canon del mundo.

## ADR-008 — Claves API y control de gasto

- Las claves no se guardan en Git ni en el JSON de exportación del mundo.
- Mostrar qué proveedor/modelo se usa.
- Añadir límites configurables de respuesta y contexto; registro de consumo informado por el proveedor cuando esté disponible.
- Avisar antes de usar un proveedor cuya API requiere facturación.
- No asumir que ChatGPT Plus incluye consumo de la API de OpenAI.
- Revisar las políticas y tarifas oficiales antes de habilitar cada proveedor.

## Criterio para reconsiderar decisiones

Reevaluar tras el primer slice funcional: un mensaje, contexto recuperado, respuesta JSON, validación, guardado y reinicio. Si la interfaz propia retrasa excesivamente la validación de canon, hacer una prueba comparativa con una extensión de SillyTavern sin cambiar el modelo de datos.
